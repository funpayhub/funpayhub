from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from funpaybotengine import Bot, Router
from funpaybotengine.dispatching import NewReviewEvent, ReviewChangedEvent

from funpayhub.app.funpay.filters.review_reply_enabled import review_reply_enabled


if TYPE_CHECKING:
    from funpayhub.app.properties.review_reply import ReviewReplyPropertiesEntry


review_reply_router = r = Router(name='fph:review_reply_router')


@r.on_new_review(review_reply_enabled)
@r.on_review_changed(review_reply_enabled)
async def reply_on_review(
    event: NewReviewEvent | ReviewChangedEvent,
    bot: Bot,
    _props: ReviewReplyPropertiesEntry,
) -> None:
    if _props.review_reply_text and _props.reply_in_review:
        asyncio.create_task(bot.review(event.message.meta.order_id, _props.review_reply_text, 5))

    if _props.chat_reply_text and _props.reply_in_chat:
        asyncio.create_task(event.message.reply(_props.chat_reply_text))

    # todo: добавить поддержку форматтеров
