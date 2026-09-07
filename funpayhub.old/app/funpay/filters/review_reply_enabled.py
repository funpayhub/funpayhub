from __future__ import annotations

from funpaybotengine import Bot
from funpaybotengine.dispatching.events import NewReviewEvent, ReviewChangedEvent


async def has_review(event: NewReviewEvent | ReviewChangedEvent, bot: Bot) -> bool:
    if event.message.meta.buyer_id == bot.userid:
        return False

    order_page = await event.get_order_page()
    if not order_page.review.rating:
        return False

    return True
