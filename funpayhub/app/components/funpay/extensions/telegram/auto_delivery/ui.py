from __future__ import annotations

import html
from typing import TYPE_CHECKING
from itertools import chain

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
from hubplatform.app.components.telegram.menu_ids import MenuIDs
from hubplatform.app.components.telegram.ui.widgets import cancel_button
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext

from funpayhub.app.components.funpay.properties import FunPayProperties

from ..menu_ids import MenuIDs as ExtensionMenuIDs
from .callbacks import AddAutoDeliveryRule, OpenAddAutoDeliveryRuleMenu


if TYPE_CHECKING:
    from funpayhub.app.components.funpay import FunPayComponent


registry = UIRegistry()


@registry.add_menu_builder(menu_id=ExtensionMenuIDs.auto_delivery.add_rule_menu)
async def add_rule_menu(
    ctx: MenuBuildContext[MenuContext],
    funpay: FunPayComponent,
) -> MenuBuildingSpec:
    menu = MenuSpec()
    menu.body_text = I18nString('➕ Выберите лот из списка ниже или введите название вручную.')

    if funpay.bot.userid != -1:
        profile = await funpay.profile()
        offers = profile.offers if profile.offers else {}
        for offer in chain(k for i in offers.values() for j in i.values() for k in j):
            if offer.title in funpay.properties.auto_delivery.subnodes:
                continue

            menu.main_keyboard.append(
                KeyboardBlockSpec.callback_button(
                    block_id=f'add_rule:{offer.id}',
                    text=html.escape(offer.title[:128] if offer.title else 'None'),
                    callback_data=AddAutoDeliveryRule(rule=offer.title or 'None'),
                ),
            )

    menu.footer_keyboard.append(
        KeyboardBlockSpec.prerendered_block(block_id='cancel', block=cancel_button()),
    )

    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())


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
                text=I18nString('Добавить правило'),
                callback_data=OpenAddAutoDeliveryRuleMenu(),
                style='success',
            ),
        )
        return state
