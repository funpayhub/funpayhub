from __future__ import annotations

from typing import TYPE_CHECKING
from html import escape

from funpaybotengine import Router
from funpaybotengine.dispatching import ReviewEvent

from funpayhub.loggers import main as logger

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.translater import _en
from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.lib.hub.text_formatters.category import InCategory

from funpayhub.app.formatters import (
    NewReviewContext,
    ReviewFormattersCategory,
    GeneralFormattersCategory,
)
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.notification_channels import NotificationChannels
from funpayhub.app.telegram.ui.builders.context import NewReviewNotificationMenuContext


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.hub.text_formatters import FormattersRegistry

    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram
    from funpayhub.app.properties.review_reply import ReviewReplyPropertiesEntry


review_reply_router = r = Router(name='fph:on_review')


_ratings = {
    1: ['review_reply', 'one_stars'],
    2: ['review_reply', 'two_stars'],
    3: ['review_reply', 'three_stars'],
    4: ['review_reply', 'four_stars'],
    5: ['review_reply', 'five_stars'],
}

_notifications = {
    1: NotificationChannels.REVIEW_1,
    2: NotificationChannels.REVIEW_2,
    3: NotificationChannels.REVIEW_3,
    4: NotificationChannels.REVIEW_4,
    5: NotificationChannels.REVIEW_5,
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
        ],
    ):
        return False

    order_page = await event.get_order_page()
    if not order_page.review.rating:
        return False
    return True


@r.on_new_review(review_filter)
@r.on_review_changed(review_filter)
async def reply_in_review(
    event: ReviewEvent,
    fp: FunPay,
    properties: FPHProps,
    fp_formatters: FormattersRegistry,
) -> None:
    order_page = await event.get_order_page()
    p: ReviewReplyPropertiesEntry = properties.get_properties(_ratings[order_page.review.rating])
    if not p.reply_in_review_enabled:
        return

    if p.review_reply_text.value == '_delete_' and order_page.review and order_page.review.reply:
        await fp.bot.delete_review(event.message.meta.order_id)
        return

    try:
        context = NewReviewContext(new_message_event=event, review_event=event)
        text = await fp_formatters.format_text(
            p.review_reply_text.value,
            context=context,
            query=InCategory(ReviewFormattersCategory).or_(InCategory(GeneralFormattersCategory)),
        )
    except Exception as e:
        logger.error(_en('An error occurred while formatting review reply text.'), exc_info=True)
        event['review_reply_error'] = e
        return

    try:
        await fp.bot.review(event.message.meta.order_id, text.entries[0], 5)
    except Exception as e:
        logger.error(_en('An error occurred while replying in review.'), exc_info=True)
        event['review_reply_error'] = e
        return

    event['review_reply_text'] = text.entries[0]


@r.on_new_review(review_filter)
@r.on_review_changed(review_filter)
async def reply_in_chat(
    event: ReviewEvent,
    fp: FunPay,
    properties: FPHProps,
    fp_formatters: FormattersRegistry,
) -> None:
    order_page = await event.get_order_page()
    p: ReviewReplyPropertiesEntry = properties.get_properties(_ratings[order_page.review.rating])
    if not p.reply_in_chat_enabled:
        return

    try:
        context = NewReviewContext(new_message_event=event, review_event=event)
        text = await fp_formatters.format_text(
            p.chat_reply_text.value,
            context=context,
            query=InCategory(ReviewFormattersCategory).or_(InCategory(GeneralFormattersCategory)),
        )
    except Exception as e:
        logger.error(
            _en('An error occurred while formatting review chat reply text.'),
            exc_info=True,
        )
        event['chat_reply_error'] = e
        return

    try:
        await fp.send_messages_stack(text, event.message.chat_id)
    except Exception as e:
        logger.error(_en('An error occurred while replying in review in chat.'), exc_info=True)
        event['chat_reply_error'] = e
        return

    event['chat_reply_text'] = text.entries[0]


@r.on_new_review(review_filter)
@r.on_review_changed(review_filter)
async def send_error_notification(event: ReviewEvent, translater: Tr, tg: Telegram):
    in_review_e = event.data.get('review_reply_error')
    in_chat_e = event.data.get('chat_reply_error')
    if not in_review_e and not in_chat_e:
        return

    texts = []
    if in_review_e:
        text = translater.translate('❌ Произошла ошибка при ответе в отзыве.') + '\n'

        if isinstance(in_review_e, TranslatableException):
            text += in_review_e.format_args(translater.translate(in_review_e.message))
        else:
            text += translater.translate('Подробности в логах.')
        texts.append(text)

    if in_chat_e:
        text = translater.translate('❌ Произошла ошибка при ответе на отзыв в чате.') + '\n'
        if isinstance(in_review_e, TranslatableException):
            text += in_review_e.format_args(translater.translate(in_review_e.message))
        else:
            text += translater.translate('Подробности в логах.')
        texts.append(text)

    total_text = escape('\n\n'.join(texts))
    tg.send_notification(NotificationChannels.ERROR, text=total_text)


@r.on_new_review(review_filter)
@r.on_review_changed(review_filter)
async def send_review_notification(event: ReviewEvent, tg: Telegram, tg_ui: UIRegistry):
    order = await event.get_order_page()
    menu = await NewReviewNotificationMenuContext(
        chat_id=-1,
        menu_id=MenuIds.review_notification,
        review_event=event,
    ).build_menu(tg_ui)

    tg.send_notification(
        _notifications[order.review.rating],
        text=menu.total_text,
        reply_markup=menu.total_keyboard(convert=True),
    )
