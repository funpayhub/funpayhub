from __future__ import annotations

import asyncio
from typing import Any
from dataclasses import dataclass
from asyncio import Future
from collections.abc import Callable, Awaitable

from funpaybotengine import Router
from funpaybotengine.dispatching import ReviewEvent
from funpaybotengine.types.pages import OrderPage
from hubplatform.expressions.manager import ExpressionsManager

lazy from funpayhub.app.components import FunPayComponent
lazy from funpayhub.app.components.funpay_component import FunPayProperties
lazy from funpayhub.app.components.funpay_component.expressions import FunPayReviewContext
lazy from funpayhub.app.components.funpay_component.properties.review_reply import ReviewReplyNode


r = router = Router('app:funpay_component:on_review')


@dataclass(frozen=True)
class ReviewReplyResult:
    filter_pass: bool = True
    review_text: str = ''
    review_sent: bool = True


NOT_FILTERED = ReviewReplyResult(filter_pass=False, review_sent=False)


@r.on_new_review.manager_inner_middleware()
@r.on_review_changed.manager_inner_middleware()
async def add_events(
    next_call: Callable[..., Any],
    context: dict[str, Any],
    event: ReviewEvent,
) -> Any:
    event['app:funpay_component:review_reply:in_chat:result'] = Future()
    event['app:funpay_component:review_reply:in_review:result'] = Future()
    return await next_call(context)


def make_middleware(in_chat: bool) -> Callable[..., Any]:
    key = f'app:funpay_component:review_reply:{"in_chat" if in_chat else "in_review"}:result'

    async def handler_outer_middleware(
        next_call: Callable[..., Any],
        context: dict[str, Any],
        event: ReviewEvent,
    ) -> Any:
        try:
            return await next_call(context)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            future: Future = event[key]
            future.set_exception(e)
            raise

    return handler_outer_middleware


def gen_context(event: ReviewEvent, order_page: OrderPage) -> FunPayReviewContext:
    return FunPayReviewContext(
        initiator_id=str(event.message.meta.buyer_id),
        initiator_username=str(event.message.meta.buyer_username),
        order_id=str(event.message.meta.order_id),
        review_rating=order_page.review.rating,  # type: ignore
        review_text=order_page.review.text or '',  # type: ignore
    )


def make_filter(in_chat: bool) -> Callable[..., Awaitable[bool | dict[str, Any]]]:
    async def real_filter(
        event: ReviewEvent,
        funpay_props: FunPayProperties,
        funpay_component: FunPayComponent,
    ) -> bool | dict[str, Any]:
        key = f'app:funpay_component:review_reply:{"in_chat" if in_chat else "in_review"}:result'
        future: Future[ReviewReplyResult] = event[key]

        if event.message.meta.buyer_id == funpay_component.bot.userid:
            future.set_result(NOT_FILTERED)
            return False

        for i in range(1, 6):
            node = funpay_props.review_reply.get_typed_node([f'review_{i}'], ReviewReplyNode)
            if (in_chat and node.reply_in_chat_enabled) or (
                not in_chat and node.reply_in_review_enabled
            ):
                break
        else:
            future.set_result(NOT_FILTERED)
            return False

        order_page = await event.get_order_page()
        if not order_page.review or not order_page.review.rating:
            future.set_result(NOT_FILTERED)
            return False

        node = funpay_props.review_reply.get_typed_node(
            [f'review_{order_page.review.rating}'],
            ReviewReplyNode,
        )
        if (in_chat and not node.reply_in_chat_enabled) or (
            not in_chat and not node.reply_in_review_enabled
        ):
            future.set_result(NOT_FILTERED)
            return False

        return {'review_node': node}

    return real_filter


@router.on_new_review(
    make_filter(in_chat=True),
    name='app:funpay_component:reply_in_chat',
    outer_middlewares=[make_middleware(in_chat=True)],
    as_task=True,
)
@router.on_review_changed(
    make_filter(in_chat=True),
    name='app:funpay_component:reply_in_chat',
    outer_middlewares=[make_middleware(in_chat=True)],
    as_task=True,
)
async def reply_on_review_in_chat(
    event: ReviewEvent,
    review_node: ReviewReplyNode,
    expressions_manager: ExpressionsManager,
    funpay_component: FunPayComponent,
) -> None:
    future: Future = event['app:funpay_component:review_reply:in_chat:result']
    order_page = await event.get_order_page()

    result_text = await expressions_manager.format_string(
        string=review_node.chat_reply_text.value,
        context=gen_context(event, order_page),
    )

    await funpay_component.bot.send_message(event.message.chat_id, result_text.result_text)
    future.set_result(ReviewReplyResult(review_text=result_text.result_text))


@router.on_new_review(
    make_filter(in_chat=False),
    name='app:funpay_component:reply_in_review',
    outer_middlewares=[make_middleware(in_chat=False)],
    as_task=True,
)
@router.on_review_changed(
    make_filter(in_chat=False),
    name='app:funpay_component:reply_in_review',
    outer_middlewares=[make_middleware(in_chat=False)],
    as_task=True,
)
async def reply_in_review(
    event: ReviewEvent,
    review_node: ReviewReplyNode,
    expressions_manager: ExpressionsManager,
    funpay_component: FunPayComponent,
) -> None:
    future: Future = event['app:funpay_component:review_reply:in_review:result']
    order_page = await event.get_order_page()

    result_text = await expressions_manager.format_string(
        string=review_node.review_reply_text.value,
        context=gen_context(event, order_page),
    )

    await funpay_component.bot.review(order_page.order_id, result_text.result_text, 0)
    future.set_result(ReviewReplyResult(review_text=result_text.result_text))
