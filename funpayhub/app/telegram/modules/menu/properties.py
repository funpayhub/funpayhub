from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram.filters import Command, CommandStart

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui import MenuContext
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from .router import router as r
from ...ui.ids import MenuIds


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery

    from funpayhub.app.main import FunPayHub
    from funpayhub.lib.properties import ListParameter
    from funpayhub.lib.telegram.ui.registry import UIRegistry
    from funpayhub.app.properties.properties import FunPayHubProperties


@r.message(CommandStart())
@r.message(Command('menu'))
async def send_menu(message: Message, tg_ui: UIRegistry) -> None:
    await MenuContext(
        menu_id=MenuIds.main_menu,
        trigger=message,
        callback_override=OpenMenu(menu_id=MenuIds.main_menu),
    ).build_and_answer(tg_ui, message)


@r.message(Command('settings'))
async def send_menu(message: Message, tg_ui: UIRegistry) -> None:
    await NodeMenuContext(
        menu_id=MenuIds.props_node,
        trigger=message,
        entry_path=[],
        callback_override=OpenMenu(menu_id=MenuIds.props_node, context_data={'entry_path': []}),
    ).build_and_answer(tg_ui, message)


@r.callback_query(cbs.ToggleNotificationChannel.filter())
async def toggle_notification_channel(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.ToggleNotificationChannel,
    hub: FunPayHub,
) -> None:
    chat_identifier = f'{query.message.chat.id}.{query.message.message_thread_id}'
    param: ListParameter[Any] = properties.telegram.notifications[callback_data.channel]

    if chat_identifier in param.value:
        await param.remove_item(chat_identifier)
    else:
        await param.add_item(chat_identifier)
    await param.save()

    await hub.telegram.fake_query(callback_data, query, pack_history=True)
