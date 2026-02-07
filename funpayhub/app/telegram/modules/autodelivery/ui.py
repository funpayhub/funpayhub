from __future__ import annotations

import html
from typing import TYPE_CHECKING
from itertools import chain

from funpayhub.lib.telegram.ui import (
    Menu,
    Button,
    MenuBuilder,
    MenuContext,
    KeyboardBuilder,
    MenuModification,
)
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.premade import AddRemoveButtonBaseModification
from funpayhub.lib.base_app.telegram.app.ui.callbacks import ClearState
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext as NodeMenuCtx
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub as FPH
    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.goods_sources import GoodsSourcesManager as GoodsManager


class AddAutoDeliveryRuleMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.add_auto_delivery_rule,
    context_type=MenuContext,
):
    async def build(self, ctx: MenuContext, translater: Tr, hub: FPH) -> Menu:
        menu = Menu(
            main_text=translater.translate('$add_auto_delivery_rule_text'),
            finalizer=StripAndNavigationFinalizer(back_button=False),
        )

        if hub.funpay.authenticated:
            profile = await hub.funpay.profile(update=False)
            for offer in chain(k for i in profile.offers.values() for j in i.values() for k in j):
                if offer.title in hub.properties.auto_delivery.entries:
                    continue

                menu.main_keyboard.add_callback_button(
                    button_id=f'add_auto_delivery_rule:{offer.id}',
                    text=html.escape(offer.title[:128]),
                    callback_data=cbs.AddAutoDeliveryRule(
                        rule=offer.title,
                        from_callback=ctx.callback_data,
                    ).pack(),
                )

        menu.footer_keyboard.add_callback_button(
            button_id='cancel',
            text=translater.translate('$clear_state'),
            callback_data=ClearState(
                delete_message=False,
                open_previous=True,
                history=ctx.callback_data_history,
            ).pack(),
        )

        return menu


class AutoDeliveryGoodsSourcesListMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.autodelivery_goods_sources_list,
    context_type=NodeMenuCtx,
):
    """
    Внимание: в context.entry_path необходимо передавать путь до текущего правила автовыдачи!
    Например: ['auto_delivery', 'my offer']
    """

    async def build(self, ctx: NodeMenuCtx, goods_manager: GoodsManager, translater: Tr) -> Menu:
        kb = KeyboardBuilder()
        for source in goods_manager.values():
            kb.add_callback_button(
                button_id=f'bind_goods_source:{source.source_id}',
                text=f'[{len(source)}] {source.display_id}',
                callback_data=cbs.BindGoodsSourceToAutoDelivery(
                    rule=ctx.entry_path[-1],
                    source_id=source.source_id,
                    from_callback=ctx.callback_data,
                ).pack(),
            )

        return Menu(
            main_text=translater.translate('$autodelivery_bind_goods_source'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )


class AddOfferButtonModification(
    MenuModification,
    modification_id='fph:add_offer_button_modification',
):
    """Модификация добавляет кнопку \'Добавить правило\' в меню настроек автовыдачи."""

    async def filter(self, ctx: NodeMenuCtx, menu: Menu, properties: FPHProps) -> bool:
        return ctx.entry_path == properties.auto_delivery.path

    async def modify(self, ctx: NodeMenuCtx, menu: Menu, translater: Tr) -> Menu:
        btn = Button.callback_button(
            button_id='add_rule',
            text=translater.translate('$add_offer_rule'),
            callback_data=cbs.OpenAddAutoDeliveryRuleMenu(from_callback=ctx.callback_data).pack(),
            row=True,
        )
        menu.footer_keyboard.insert(0, btn)
        return menu


class ReplaceSourcesListButtonModification(
    MenuModification,
    modification_id='fph:replace_sources_list_button_modification',
):
    """
    Заменяет кнопку параметра goods_source в `auto_delivery.*` на кастомную кнопку.
    """

    async def filter(self, ctx: NodeMenuCtx, menu: Menu, properties: FPHProps) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == properties.auto_delivery.id

    async def modify(
        self,
        ctx: NodeMenuCtx,
        menu: Menu,
        translater: Tr,
    ) -> Menu:
        entry_path = str([*ctx.entry_path, 'goods_source'])

        for l_index, line in enumerate(menu.main_keyboard):
            for b_index, button in enumerate(line):
                if not button.button_id.endswith(entry_path):
                    continue

                btn = Button.callback_button(
                    button_id='bind_goods_source',
                    text=translater.translate('$bind_goods_source'),
                    callback_data=cbs.AutoDeliveryOpenGoodsSourcesList(
                        rule=ctx.entry_path[-1],
                        from_callback=ctx.callback_data,
                    ).pack(),
                )
                menu.main_keyboard.keyboard[l_index][b_index] = btn
                break
        return menu


class AddRemoveButtonToAutoDeliveryModification(
    AddRemoveButtonBaseModification,
    modification_id='fph:add_remove_button_to_auto_delivery',
):
    async def filter(self, ctx: NodeMenuCtx, menu: Menu) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == 'auto_delivery'

    async def modify(self, ctx: NodeMenuCtx, menu: Menu, translater: Tr) -> Menu:
        delete_callback = cbs.DeleteAutoDeliveryRule(
            rule=ctx.entry_path[1],
            from_callback=ctx.callback_data,
        ).pack()

        return await self._modify(ctx, menu, translater, delete_callback=delete_callback)
