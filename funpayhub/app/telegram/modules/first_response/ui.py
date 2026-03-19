from __future__ import annotations


__all__ = [
    'BindToOfferButtonModification',
    'AddRemoveButtonToFirstResponseModification',
    'BindToOfferMenu',
    'ReplaceNameWithOfferNameModification',
    'ModifyHeaderText',
]


import html
from typing import TYPE_CHECKING
from itertools import chain

from funpayhub.lib.telegram.ui import Menu, MenuBuilder, MenuContextOld, MenuModification
from funpayhub.lib.telegram.callback_data import join_callbacks
from funpayhub.lib.base_app.telegram.app.ui.callbacks import ClearState
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer
from funpayhub.lib.translater import translater

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.premade import AddRemoveButtonBaseModification, confirmable_button
from funpayhub.app.properties.first_response import FirstResponseToOfferNode

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

    from funpayhub.app.main import FunPayHub as FPH
    from funpayhub.app.properties import FunPayHubProperties as FPHProps


ru = translater.translate


class BindToOfferButtonModification(MenuModification, modification_id='fph:bind_to_offer'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return ctx.entry_path == properties.first_response.path

    async def modify(self, ctx: NodeMenuContext, menu: Menu) -> Menu:
        menu.footer_keyboard.add_callback_button(
            button_id='bind_to_offer',
            text=ru('➕ Привязать к лоту'),
            callback_data=cbs.OpenAddGreetingsToOfferMenu(ui_history=ctx.as_ui_history()).pack(),
        )

        buttons = confirmable_button(
            ctx=ctx,
            button_id='clear_cache',
            text=ru('🗑️ Очистить кэш'),
            callback_data=cbs.ClearFirstResponseCache(ui_history=ctx.as_ui_history()).pack(),
            style='danger',
        )
        menu.footer_keyboard.add_row(*buttons)
        return menu


class AddRemoveButtonToFirstResponseModification(
    AddRemoveButtonBaseModification,
    modification_id='fph:add_remove_fr',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == properties.first_response.path[0]

    async def modify(self, ctx: NodeMenuContext, menu: Menu) -> Menu:
        return await self._modify(
            ctx,
            menu,
            'delete_greetings',
            cbs.RemoveGreetings(offer_id=ctx.entry_path[-1], ui_history=ctx.ui_history).pack(),
        )


class ModifyHeaderText(MenuModification, modification_id='fph:first_response_modify_header'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps):
        return (
            len(ctx.entry_path) == 2
            and ctx.entry_path[0] == properties.first_response.path[0]
            and isinstance(properties.get_node(ctx.entry_path), FirstResponseToOfferNode)
        )

    async def modify(self, ctx: NodeMenuContext, menu: Menu, hub: FPH):
        if not hub.funpay.authenticated:
            return menu

        profile = await hub.funpay.profile()
        offers = {}
        if profile.offers:
            offers = {
                str(offer.id): offer
                for subcat_offers in profile.offers.values()
                for offers_tuple in subcat_offers.values()
                for offer in offers_tuple
            }

        offer_id = ctx.entry_path[-1].lstrip('__offer__')
        if offer_id not in offers:
            menu.header_text = f'⚠️ <b><u>{offer_id}</u></b>'
        else:
            menu.header_text = f'<b>[{offer_id}] {html.escape(offers[offer_id].title)}</b>'
        return menu


class ReplaceNameWithOfferNameModification(
    MenuModification,
    modification_id='fph:replace_name_with_offer_name',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return ctx.entry_path == properties.first_response.path

    async def modify(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps, hub: FPH):
        if not hub.funpay.authenticated:
            return menu

        profile = await hub.funpay.profile()
        offers = {}
        if profile.offers:
            offers = {
                str(offer.id): offer
                for subcat_offers in profile.offers.values()
                for offers_tuple in subcat_offers.values()
                for offer in offers_tuple
            }

        pattern = 'param_change:' + '.'.join(properties.first_response.path) + '.__offer__'
        for line in menu.main_keyboard.keyboard:
            for button in line:
                if not button.button_id.startswith(pattern):
                    continue

                offer_id = button.button_id.split(pattern)[-1]
                if offer_id not in offers:
                    button.obj.text = '⚠️ ' + offer_id
                else:
                    button.obj.text = f'[{offer_id}] ' + offers[offer_id].title[:100]

        return menu


class BindToOfferMenu(
    MenuBuilder,
    menu_id=MenuIds.bind_first_response_to_offer,
    context_type=MenuContextOld,
):
    async def build(
        self,
        ctx: MenuContextOld,
        translater: Tr,
        hub: FPH,
        properties: FPHProps,
    ) -> Menu:
        menu = Menu(finalizer=StripAndNavigationFinalizer())
        menu.main_text = translater.translate(
            '⌨️ Выберите лот, к которому хотите привязать ответ на первое сообщение '
            'или введите <b>ID лота</b>.',
        )
        menu.footer_keyboard.add_callback_button(
            button_id='cancel',
            text=translater.translate('🔘 Отмена'),
            callback_data=ClearState().pack(),
        )

        if not hub.funpay.authenticated:
            return menu

        profile = await hub.funpay.profile()
        if not profile.offers:
            return menu

        fr_props = properties.first_response

        for offer_dict in profile.offers.values():
            for offer in chain(*offer_dict.values()):
                if f'__offer__{offer.id}' in fr_props._nodes:
                    continue

                menu.main_keyboard.add_callback_button(
                    button_id=f'bind_to_offer:{offer.id}',
                    text=offer.title,
                    callback_data=cbs.BindFirstResponseToOffer(
                        offer_id=str(offer.id),
                        history=ctx.callback_data_history,
                    ).pack(),
                )

        return menu
