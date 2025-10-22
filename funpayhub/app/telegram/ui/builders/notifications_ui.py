from __future__ import annotations

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.properties import ListParameter
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContext

from .. import premade


async def current_chat_notifications_menu_builder(
    ctx: MenuContext,
    properties: FunPayHubProperties,
    translater: Translater,
) -> Menu:
    props = properties.telegram.notifications
    kb = []
    chat = f'{ctx.chat_id}.{ctx.thread_id}'
    language = properties.general.language.real_value
    callback_data = ctx.callback_data

    notification_buttons = [
        Button(
            button_id=f'toggle-notification:{i}',
            obj=InlineKeyboardButton(
                text=f'{'🔔' if chat in props.entries[i].value else'🔕'} {index+1}⭐',
                callback_data=cbs.ToggleNotificationChannel(
                    channel=i,
                    history=callback_data.as_history() if callback_data is not None else [],
                ).pack(),
            )
        )
        for index, i in enumerate(['review_1', 'review_2', 'review_3', 'review_4', 'review_5'])
    ]
    kb.append(notification_buttons)

    for entry in props.entries.values():
        if entry.id in ['review_1', 'review_2', 'review_3', 'review_4', 'review_5']:
            continue
        if not isinstance(entry, ListParameter):
            continue

        indicator = '🔔' if chat in entry.value else '🔕'
        notifications_channel = translater.translate(entry.name, language)

        kb.append([
            Button(
                button_id=f'toggle_notification:{entry.id}',
                obj=InlineKeyboardButton(
                    text=f'{indicator} {notifications_channel}',
                    callback_data=cbs.ToggleNotificationChannel(
                        channel=entry.id,
                        history=callback_data.as_history() if callback_data is not None else [],
                    ).pack(),
                ),
            )]
        )

    return Menu(
        text='$notifications',
        main_keyboard=kb,
        finalizer=premade.default_finalizer_factory(),
    )
