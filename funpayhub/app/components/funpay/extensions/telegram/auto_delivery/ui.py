from __future__ import annotations

from hubplatform.i18n import I18nString
from hubplatform.telegram.ui import (
    UIRegistry,
    MenuBuildContext,
    KeyboardBlockSpec,
    MenuBuildingState,
)
from hubplatform.app.components.telegram.menu_ids import MenuIDs
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext

from funpayhub.app.components.funpay.properties import FunPayProperties

from .callbacks import OpenAddAutoDeliveryRuleMenu


registry = UIRegistry()


@registry.add_menu_modification(
    menu_id=MenuIDs.properties.properties_menu,
    modification_id='fph:add_offer_button_modification',
)
class AddOfferButtonModification:
    async def filter(
        self,
        ctx: MenuBuildContext[NodeMenuContext],
        menu: MenuBuildingState,
        funpay_props: FunPayProperties,
    ) -> bool:
        return tuple(ctx.context.node_path) == funpay_props.auto_delivery.path

    async def __call__(
        self,
        ctx: MenuBuildContext[NodeMenuContext],
        state: MenuBuildingState,
    ) -> MenuBuildingState:
        state.menu.footer_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id='add_rule',
                text=I18nString('➕ Добавить правило'),
                callback_data=OpenAddAutoDeliveryRuleMenu(),
                style='success',
            ),
        )
        return state
