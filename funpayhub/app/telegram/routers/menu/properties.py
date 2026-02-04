from __future__ import annotations

from typing import TYPE_CHECKING, Any
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Update,
    Message,
    CallbackQuery,
)
from aiogram.filters import Command, CommandStart

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.properties import ListParameter
from funpayhub.lib.telegram.ui import MenuContext
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.app.telegram.ui.builders.properties_ui.context import EntryMenuContext

from .router import router as r
from ...ui.ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.app.properties.properties import FunPayHubProperties


async def _delete_message(msg: Message) -> None:
    with suppress(Exception):
        await msg.delete()


# TEMP


@r.message(CommandStart())
@r.message(Command('menu'))
async def send_menu(message: Message, tg_ui: UIRegistry) -> None:
    await MenuContext(
        menu_id=MenuIds.main_menu,
        trigger=message,
        callback_override=cbs.OpenMenu(menu_id=MenuIds.main_menu),
    ).build_and_answer(tg_ui, message)


# TEMP


@r.message(Command('settings'))
async def send_menu(message: Message, tg_ui: UIRegistry) -> None:
    await EntryMenuContext(
        menu_id=MenuIds.properties_entry,
        trigger=message,
        entry_path=[],
        callback_override=cbs.OpenMenu(
            menu_id=MenuIds.properties_entry,
            context_data={'entry_path': []},
        ),
    ).build_and_answer(tg_ui, message)


@r.callback_query(cbs.ToggleNotificationChannel.filter())
async def toggle_notification_channel(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.ToggleNotificationChannel,
    dispatcher: Dispatcher,
    bot: Bot,
) -> None:
    chat_identifier = f'{query.message.chat.id}.{query.message.message_thread_id}'
    param: ListParameter[Any] = properties.telegram.notifications[callback_data.channel]

    if chat_identifier in param.value:
        await param.remove_item(chat_identifier)
    else:
        await param.add_item(chat_identifier)
    await param.save()

    await dispatcher.feed_update(
        bot,
        Update(
            update_id=-1,
            callback_query=query.model_copy(update={'data': callback_data.pack_history()}),
        ),
    )
