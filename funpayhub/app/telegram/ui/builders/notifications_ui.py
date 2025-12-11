from __future__ import annotations

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.properties import ListParameter
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import KeyboardBuilder
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, MenuContext

from .. import premade
from ..ids import MenuIds


class NotificationsMenuBuilder(MenuBuilder):
    id = MenuIds.tg_chat_notifications
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        properties: FunPayHubProperties,
        translater: Translater,
    ) -> Menu:
        props = properties.telegram.notifications
        kb = KeyboardBuilder()
        chat = f'{ctx.chat_id}.{ctx.thread_id}'
        callback_data = ctx.callback_data

        kb.add_row(
            *(
                Button.callback_button(
                    button_id=f'toggle-notification:{i}',
                    text=f'{"🔔" if chat in props.entries[i].value else "🔕"} {index + 1}⭐',
                    callback_data=cbs.ToggleNotificationChannel(
                        channel=i,
                        history=callback_data.as_history() if callback_data is not None else [],
                    ).pack(),
                )
                for index, i in enumerate(f'review_{j}' for j in range(1, 6))
            )
        )

        for entry in props.entries.values():
            if entry.id in [f'review_{j}' for j in range(1, 6)]:
                continue
            if not isinstance(entry, ListParameter):
                continue

            indicator = '🔔' if chat in entry.value else '🔕'
            notifications_channel = translater.translate(entry.name)
            kb.add_callback_button(
                button_id=f'toggle_notification:{entry.id}',
                text=f'{indicator} {notifications_channel}',
                callback_data=cbs.ToggleNotificationChannel(
                    channel=entry.id,
                    history=callback_data.as_history() if callback_data is not None else [],
                ).pack(),
            )

        return Menu(
            text='$notifications',
            main_keyboard=kb,
            finalizer=premade.StripAndNavigationFinalizer(),
        )
