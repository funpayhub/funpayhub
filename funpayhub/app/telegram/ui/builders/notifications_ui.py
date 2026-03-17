from __future__ import annotations

from funpayhub.lib.properties import ListParameter
from funpayhub.lib.telegram.ui import KeyboardBuilder, MenuContextModel
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer
from funpayhub.lib.translater import translater

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties

from ..ids import MenuIds


ru = translater.translate


class NotificationsMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.tg_chat_notifications,
    context_type=MenuContextModel,
):
    async def build(self, ctx: MenuContextModel, properties: FunPayHubProperties) -> Menu:
        props = properties.telegram.notifications
        menu = Menu(
            main_text=ru('<b><u>🔔 Уведомления</u></b>'),
            main_keyboard=KeyboardBuilder(),
            finalizer=StripAndNavigationFinalizer(),
        )
        chat = f'{ctx.chat_id}.{ctx.thread_id}'

        menu.main_keyboard.add_row(
            *(
                Button.callback_button(
                    button_id=f'toggle-notification:{i}',
                    text=f'{"🔔" if chat in props.entries[i].value else "🔕"} {index + 1}⭐',
                    callback_data=cbs.ToggleNotificationChannel(
                        channel=i,
                        ui_history=ctx.as_ui_history(),
                    ).pack(),
                )
                for index, i in enumerate(f'review_{j}' for j in range(1, 6))
            ),
        )

        for entry in props.entries.values():
            if entry.id in [f'review_{j}' for j in range(1, 6)]:
                continue
            if not isinstance(entry, ListParameter):
                continue

            menu.main_keyboard.add_callback_button(
                button_id=f'toggle_notification:{entry.id}',
                text=f'{'🔔' if chat in entry.value else '🔕'} {ru(entry.name)}',
                callback_data=cbs.ToggleNotificationChannel(
                    channel=entry.id,
                    ui_history=ctx.as_ui_history()
                ).pack(),
            )

        return menu
