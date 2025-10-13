from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import Message, CallbackQuery

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.properties import ListParameter
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, UIContext

from .. import premade

if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


async def build_current_chat_notifications_keyboard(
    ui: UIRegistry,
    ctx: UIContext,
    properties: FunPayHubProperties,
    chat_id: int,
    thread_id: int | None
) -> Keyboard:
    props = properties.telegram.notifications
    kb = []
    chat = f'{chat_id}.{thread_id}'

    for entry in props.entries.values():
        if not isinstance(entry, ListParameter):
            continue

        indicator = '🔔' if chat in entry.value else '🔕'
        notifications_channel = ui.translater.translate(entry.name, ctx.language)

        kb.append([
            Button(
                button_id=f'toggle_notification:{entry.id}',
                text=f'{indicator} {notifications_channel}',
                callback_data=cbs.ToggleNotificationChannel(
                    channel=entry.id,
                    history=ctx.callback.as_history()
                ).pack()
            )
        ])
    return kb



async def current_chat_notifications_menu_builder(
    ui: UIRegistry,
    ctx: UIContext,
    properties: FunPayHubProperties,
    message: Message | None = None,
    query: CallbackQuery | None = None,
) -> Menu:
    if query:
        message = query.message

    if message is None:
        raise ValueError('Unable to build current chat notifications menu.')

    chat_id, thread_id = message.chat.id, message.message_thread_id

    return Menu(
        ui=ui,
        context=ctx,
        text='Ну типа уводмления',
        image=None,
        keyboard=await build_current_chat_notifications_keyboard(
            ui,
            ctx,
            properties,
            chat_id,
            thread_id
        ),
        finalizer=premade.default_finalizer_factory(),
    )
