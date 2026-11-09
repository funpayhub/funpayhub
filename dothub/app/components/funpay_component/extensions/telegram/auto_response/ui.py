from __future__ import annotations

from typing import TYPE_CHECKING

from hubplatform.i18n import I18nString
from hubplatform.telegram.ui import (
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
    MenuBuildingState,
)
from hubplatform.app.components.telegram.menu_ids import PropertiesMenuIDs
from hubplatform.app.components.telegram.ui.widgets import cancel_button
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext

from ..menu_ids import MenuIDs as ExtensionMenuIDs
from .callbacks import AddCommand


if TYPE_CHECKING:
    from dothub.app.components.funpay_component import FunPayProperties

registry = UIRegistry()


@registry.add_menu_builder(
    menu_id=ExtensionMenuIDs.auto_response.add_rule_menu,
    context_type=MenuContext,
)
async def add_command_menu(
    ctx: MenuBuildContext[MenuContext],
) -> None:
    menu = MenuSpec()
    menu.body_text = (
        '<h1>⚡️ Новая команда автоответа</h1><b>✍️ Отправьте команду, которую хотите добавить.</b>'
    )

    menu.footer_keyboard.append(
        KeyboardBlockSpec.prerendered_block(block_id='cancel', block=cancel_button()),
    )
    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())


@registry.add_menu_modification(
    menu_id=PropertiesMenuIDs.properties_menu,
    modification_id='funpay_component:add_command_button',
)
class AddCommandButtonModification:
    async def filter(
        self,
        ctx: MenuBuildContext[NodeMenuContext],
        menu: MenuBuildingState,
        funpay_props: FunPayProperties,
    ) -> bool:
        return tuple(ctx.context.node_path) == funpay_props.auto_response.path

    async def __call__(
        self,
        ctx: MenuBuildContext[NodeMenuContext],
        state: MenuBuildingState,
    ) -> MenuBuildingState:
        state.menu.footer_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id='funpay_component:add_command',
                text=I18nString('➕ Добавить команду'),
                callback_data=AddCommand(),
            ),
        )
        return state
