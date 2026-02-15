from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from funpaybotengine import Bot, Router
from funpaybotengine.dispatching import NewReviewEvent, ReviewChangedEvent

from funpayhub.app.funpay.filters.review_reply_enabled import has_review


if TYPE_CHECKING:
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.app.main import FunPayHub


review_reply_router = r = Router(name='fph:on_review')


async def review_filter(
    event: NewReviewEvent | ReviewChangedEvent,
    properties: FunPayHubProperties,
    hub: FunPayHub
) -> bool:
    if event.message.meta.buyer_id == hub.funpay.bot.userid:
        return False

    if not any([
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
    ]):
        return False

    order_page = await event.get_order_page()
    if not order_page.review.rating:
        return False

    return True


@r.on_new_review(review_filter)
@r.on_review_changed(review_filter)
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