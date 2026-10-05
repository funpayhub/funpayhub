from __future__ import annotations

from aiogram.types import CallbackQuery as Query
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager

from funpayhub.app.components.telegram_component.properties import TelegramProperties

from .callbacks import ToggleNotificationsChannel, BulkChangeNotificationsCategory


router = Router(name='app:notifications_ui')


@router.callback_query(
    ToggleNotificationsChannel.filter(),
)
async def toggle_notifications_channel(
    q: Query,
    telegram_properties: TelegramProperties,
    cbd: ToggleNotificationsChannel,
    telegram_ui_manager: UIManager,
) -> None:
    channel = telegram_properties.notifications.get_channel(cbd.channel_path)
    chat_id, thread_id = q.message.chat.id, q.message.message_thread_id
    if channel.has_chat(chat_id, thread_id):
        await channel.remove_chat(chat_id, thread_id)
    else:
        await channel.add_chat(chat_id, thread_id)

    await telegram_ui_manager.rerender_session(cbd.session_id, trigger=q)
    await q.answer()


@router.callback_query(
    BulkChangeNotificationsCategory.filter(),
)
async def bulk_toggle_notifications_category(
    q: Query,
    telegram_properties: TelegramProperties,
    cbd: BulkChangeNotificationsCategory,
    telegram_ui_manager: UIManager,
):
    category = telegram_properties.notifications.get_category(cbd.category_path)
    chat_id, thread_id = q.message.chat.id, q.message.message_thread_id

    for channel in category.channels(recursive=True):
        if cbd.enable:
            await channel.add_chat(chat_id, thread_id, save=False)
        else:
            await channel.remove_chat(chat_id, thread_id, save=False)

    await telegram_properties.notifications.save()
    await telegram_ui_manager.rerender_session(cbd.session_id, trigger=q)
    await q.answer()
