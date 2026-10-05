from __future__ import annotations

from hubplatform.i18n import I18nString
from hubplatform.telegram.ui import (
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
)
from hubplatform.app.components.telegram.menu_ids import MenuIDs as PlatformMenuIDs
from hubplatform.app.components.telegram.ui.callbacks import OpenMenu
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext
from hubplatform.app.components.telegram.expressions.builders import ExpressionsListMenuContext

from ..notifications_ui.ui import NotificationsMenuContext
from ..notifications_ui.menu_ids import NotificationsUIMenuIDs


registry = UIRegistry()


@registry.add_menu_builder(menu_id='app:main_menu')
async def build_main_menu(ctx: MenuBuildContext[MenuContext]) -> MenuBuildingSpec:
    menu = MenuSpec()
    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:open_properties',
            text=I18nString('⚙️ Настройки'),
            callback_data=OpenMenu(
                menu_id=PlatformMenuIDs.properties.properties_menu,
                context=NodeMenuContext(node_path=[]).dump(),
            ),
        ),
    )

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:open_current_chat_notifications',
            text=I18nString('🔔 Уведомления'),
            callback_data=OpenMenu(
                menu_id=NotificationsUIMenuIDs.current_chat_notifications,
                context=NotificationsMenuContext(category_path=[]).dump(),
            ),
        ),
    )

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:open_goods_sources',
            text=I18nString('📦 Источники товаров'),
            callback_data=OpenMenu(
                menu_id=PlatformMenuIDs.goods_sources.sources_list_menu,
                context=MenuContext().dump(),
            ),
        ),
    )

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:open_expressions_list',
            text=I18nString('♾️ Выражения'),
            callback_data=OpenMenu(
                menu_id=PlatformMenuIDs.expressions.expressions_list_menu,
                context=ExpressionsListMenuContext().dump(),
            ),
        ),
    )

    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())
