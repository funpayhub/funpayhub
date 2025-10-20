from __future__ import annotations

from typing import TYPE_CHECKING

from funpaybotengine import Bot
from funpaybotengine.dispatching.events import NewReviewEvent, ReviewChangedEvent

from funpayhub.app.properties import FunPayHubProperties


if TYPE_CHECKING:
    from funpayhub.app.properties.review_reply import ReviewReplyPropertiesEntry


ratings = {
    1: 'review_reply.one_stars',
    2: 'review_reply.two_stars',
    3: 'review_reply.three_stars',
    4: 'review_reply.four_stars',
    5: 'review_reply.five_stars',
}


async def review_reply_enabled(
    event: NewReviewEvent | ReviewChangedEvent,
    properties: FunPayHubProperties,
    bot: Bot,
):
    if event.message.meta.buyer_id == bot.userid:
        return False

    order_page = await event.get_order_page()
    if not order_page.review.rating:
        return None

    props: ReviewReplyPropertiesEntry = properties.get_properties(
        ratings[order_page.review.rating]
    )
    if not any(
        [
            props.reply_in_review and props.review_reply_text,
            props.reply_in_chat and props.chat_reply_text,
        ]
    ):
        return False

    return {'_props': props}
