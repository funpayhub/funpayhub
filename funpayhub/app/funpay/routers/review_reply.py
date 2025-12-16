from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from funpaybotengine import Bot, Router
from funpaybotengine.dispatching import NewReviewEvent, ReviewChangedEvent

from funpayhub.app.funpay.filters.review_reply_enabled import has_review


if TYPE_CHECKING:
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.app.properties.review_reply import ReviewReplyPropertiesEntry


review_reply_router = r = Router(name='fph:review_reply_router')


_ratings = {
    1: ['review_reply', 'one_stars'],
    2: ['review_reply', 'two_stars'],
    3: ['review_reply', 'three_stars'],
    4: ['review_reply', 'four_stars'],
    5: ['review_reply', 'five_stars'],
}


@r.on_new_review(has_review)
@r.on_review_changed(has_review)
async def reply_on_review(
    event: NewReviewEvent | ReviewChangedEvent,
    bot: Bot,
    properties: FunPayHubProperties,
) -> None:
    order_page = await event.get_order_page()
    p: ReviewReplyPropertiesEntry = properties.get_properties(_ratings[order_page.review.rating])
    if not any(
        [
            p.reply_in_review.value and p.review_reply_text.value,
            p.reply_in_chat.value and p.chat_reply_text.value,
        ],
    ):
        return

    if p.review_reply_text.value and p.reply_in_review.value:
        if p.review_reply_text.value == '-' and order_page.review and order_page.review.reply:
            asyncio.create_task(bot.delete_review(event.message.meta.order_id))
        else:
            asyncio.create_task(
                bot.review(event.message.meta.order_id, p.review_reply_text.value, 5),
            )

    if p.chat_reply_text.value and p.reply_in_chat.value:
        asyncio.create_task(event.message.reply(p.chat_reply_text.value))

    # todo: добавить поддержку форматтеров
