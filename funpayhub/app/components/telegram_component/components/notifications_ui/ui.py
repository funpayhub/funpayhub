from __future__ import annotations


__all__ = [
    'registry',
]

from hubplatform.i18n import I18nString
from hubplatform.telegram.ui import (
    Button,
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
)
from hubplatform.app.components.telegram.ui.callbacks import OpenMenu
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer

from funpayhub.app.components.telegram_component.properties import TelegramProperties

from .menu_ids import NotificationsUIMenuIDs
from .callbacks import ToggleNotificationsChannel, BulkChangeNotificationsCategory


registry = UIRegistry()


class NotificationsMenuContext(MenuContext):
    category_path: list[str]


@registry.add_menu_builder(
    menu_id=NotificationsUIMenuIDs.current_chat_notifications,
    context_type=NotificationsMenuContext,
)
async def build_curr_chat_notifications_menu(
    ctx: MenuBuildContext[NotificationsMenuContext],
    telegram_properties: TelegramProperties,
) -> MenuBuildingSpec:
    menu = MenuSpec()
    notification_properties = telegram_properties.notifications
    category = notification_properties.get_category(ctx.context.category_path)
    chat_id, thread_id = ctx.environment.chat_id, ctx.environment.thread_id

    menu.header_text = I18nString(
        f'<h1>Уведомления в текущем чате (<code>{chat_id}.{thread_id}</code>)</h1>',
    )

    for channel in category.channels():
        menu.main_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id=f'toggle_notification_channel:{channel.id}',
                text=channel.name,
                callback_data=ToggleNotificationsChannel(
                    channel_path=list(channel.get_notifications_path()),
                ),
                style='success' if channel.has_chat(chat_id, thread_id) else 'danger',
            ),
        )

    for subcategory in category.subcategories():
        menu.main_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id=f'open_notifications_category:{subcategory.get_notifications_path()}',
                text=subcategory.name,
                callback_data=OpenMenu(
                    menu_id=NotificationsUIMenuIDs.current_chat_notifications,
                    context=NotificationsMenuContext(
                        category_path=subcategory.get_notifications_path(),
                    ).dump(),
                ),
            ),
        )

    menu.footer_keyboard.append(
        KeyboardBlockSpec.prerendered_block(
            block_id='bunk_toggle_notifications',
            block=[
                Button(
                    button_id='bunk_enable_notifications',
                    text=I18nString('Включить всё'),
                    callback_data=BulkChangeNotificationsCategory(
                        category_path=ctx.context.category_path,
                        enable=True,
                    ),
                    style='success',
                ),
                Button(
                    button_id='bunk_disable_notifications',
                    text=I18nString('Выключить всё'),
                    callback_data=BulkChangeNotificationsCategory(
                        category_path=ctx.context.category_path,
                        enable=False,
                    ),
                    style='danger',
                ),
            ],
        ),
    )

    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())
