from __future__ import annotations

from typing import TYPE_CHECKING

from funpaybotengine import Router
from funpaybotengine.dispatching import ReviewEvent


if TYPE_CHECKING:
    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.properties.review_reply import ReviewReplyPropertiesEntry


review_reply_router = r = Router(name='fph:on_review')


_ratings = {
    1: ['review_reply', 'one_stars'],
    2: ['review_reply', 'two_stars'],
    3: ['review_reply', 'three_stars'],
    4: ['review_reply', 'four_stars'],
    5: ['review_reply', 'five_stars'],
}


async def review_filter(event: ReviewEvent, properties: FPHProps, fp: FunPay) -> bool:
    if event.message.meta.buyer_id == fp.bot.userid:
        return False

    if not any(
        [
            properties.review_reply.five_stars.reaction_enabled,
            properties.review_reply.four_stars.reaction_enabled,
            properties.review_reply.three_stars.reaction_enabled,
            properties.review_reply.two_stars.reaction_enabled,
            properties.review_reply.one_stars.reaction_enabled,
            properties.telegram.notifications.review_5.value,
            properties.telegram.notifications.review_4.value,
            properties.telegram.notifications.review_3.value,
            properties.telegram.notifications.review_2.value,
            properties.telegram.notifications.review_1.value,
        ]
    ):
        return False

    order_page = await event.get_order_page()
    if not order_page.review.rating:
        return False

    return True


@r.on_new_review(review_filter)
@r.on_review_changed(review_filter)
async def reply_in_review(event: ReviewEvent, fp: FunPay, properties: FPHProps) -> None:
    order_page = await event.get_order_page()
    p: ReviewReplyPropertiesEntry = properties.get_properties(_ratings[order_page.review.rating])
    if not p.reply_in_review_enabled:
        return

    if p.review_reply_text.value == '_delete_' and order_page.review and order_page.review.reply:
        await fp.bot.delete_review(event.message.meta.order_id)
    else:
        (await fp.bot.review(event.message.meta.order_id, p.review_reply_text.value, 5),)


@r.on_new_review(review_filter)
@r.on_review_changed(review_filter)
async def reply_in_chat(event: ReviewEvent, fp: FunPay, properties: FPHProps) -> None:
    order_page = await event.get_order_page()
    p: ReviewReplyPropertiesEntry = properties.get_properties(_ratings[order_page.review.rating])
    if not p.reply_in_chat_enabled:
        return

    await fp.send_message(event.message.chat_id, p.chat_reply_text.value)


@r.on_new_review(review_filter)
@r.on_review_changed(review_filter)
async def send_notification(): ...
