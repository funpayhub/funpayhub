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
from hubplatform.goods_source import GoodsSourcesManager
from hubplatform.app.components.telegram.menu_ids import MenuIDs
from hubplatform.app.components.telegram.ui.widgets import cancel_button, confirmable_button
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext

from funpayhub.app.components.funpay.properties import FunPayProperties

from ..menu_ids import MenuIDs as ExtensionMenuIDs
from .callbacks import (
    OpenBindGoodsMenu,
    AddAutoDeliveryRule,
    DeleteAutoDeliveryRule,
    OpenAddAutoDeliveryRuleMenu,
    BindGoodsSourceToAutoDelivery,
)


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


@registry.add_menu_builder(
    menu_id=ExtensionMenuIDs.auto_delivery.bind_source_list_menu,
    context_type=NodeMenuContext,
)
async def bind_source_list_menu(
    ctx: MenuBuildContext[NodeMenuContext],
    goods_manager: GoodsSourcesManager,
):
    menu = MenuSpec()
    menu.body_text = I18nString(
        '🗳 Выберите источник товаров из списка или введтите название вручную.',
    )

    for source in goods_manager.values():
        menu.main_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id=f'bind_goods_source:{source.source_id}',
                text=f'[{await source.len()}] {source.source_id}',
                callback_data=BindGoodsSourceToAutoDelivery(
                    rule=ctx.context.node_path[-1],
                    source_id=source.source_id,
                ),
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


async def is_ad_node_filter(
    ctx: MenuBuildContext[NodeMenuContext],
    state: MenuBuildingState,
    funpay_props: FunPayProperties,
) -> bool:
    ad_props_path = funpay_props.auto_delivery.path
    if len(ctx.context.node_path) != (len(ad_props_path) + 1):
        return False

    if tuple(ctx.context.node_path[: len(ad_props_path)]) != ad_props_path:
        return False
    return True


@registry.add_menu_modification(
    menu_id=MenuIDs.properties.properties_menu,
    modification_id='app:replace_sources_list_button',
    filter=is_ad_node_filter,
)
async def replace_sources_list_button_modification(
    ctx: MenuBuildContext[NodeMenuContext],
    state: MenuBuildingState,
) -> MenuBuildingState:
    entry_path = [*ctx.context.node_path, 'goods_source']
    for index, block in enumerate(state.menu.main_keyboard):
        if block.block_id != f'hubplatform.properties.{":".join(entry_path)}':
            continue

        btn = KeyboardBlockSpec.callback_button(
            block_id='bind_goods_source',
            text=I18nString('🗳 Источник товаров'),
            callback_data=OpenBindGoodsMenu(rule=ctx.context.node_path[-1]).pack(),
        )
        state.menu.main_keyboard[index] = btn
        break
    return state


@registry.add_menu_modification(
    menu_id=MenuIDs.properties.properties_menu,
    modification_id='app:auto_delivery.node.add_remove_button',
    filter=is_ad_node_filter,
)
async def add_remove_button_to_ad_node(
    ctx: MenuBuildContext[NodeMenuContext], state: MenuBuildingState
) -> MenuBuildingState:
    state.menu.footer_keyboard.append(
        KeyboardBlockSpec.prerendered_block(
            block_id='delete_rule',
            block=confirmable_button(
                id='delete_rule',
                ctx=ctx.context,
                text=I18nString('Удалить'),
                callback_data=DeleteAutoDeliveryRule(rule=ctx.context.node_path[-1]),
                style='danger',
            ),
        ),
    )
    return state
