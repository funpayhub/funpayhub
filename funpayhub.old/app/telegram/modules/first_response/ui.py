from __future__ import annotations


__all__ = [
    'GreetingsMenuMod',
    'BindToOfferMenu',
    'ReplaceNameWithOfferNameModification',
    'GreetingsNodeMenuMod',
]


import html
from typing import TYPE_CHECKING
from itertools import chain

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import Menu, MenuBuilder, MenuContext, MenuModification
from funpayhub.lib.base_app.telegram.app.ui.callbacks import ClearState
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.premade import confirmable_button
from funpayhub.app.properties.first_response import FirstResponseToOfferNode

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

    from funpayhub.app.main import FunPayHub as FPH
    from funpayhub.app.properties import FunPayHubProperties as FPHProps


ru = translater.translate


class GreetingsMenuMod(MenuModification, modification_id='fph:greetings_menu_mod'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return ctx.entry_path == properties.first_response.path

    async def modify(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> Menu:
        menu.footer_keyboard.add_callback_button(
            button_id='bind_to_offer',
            text=ru('➕ Привязать к лоту'),
            callback_data=cbs.OpenAddGreetingsToOfferMenu(ui_history=ctx.as_ui_history()).pack(),
        )

        buttons = confirmable_button(
            ctx=ctx,
            button_id='clear_cache',
            text=ru('🗑️ Очистить кэш'),
            callback_data=cbs.ClearGreetingsCache(ui_history=ctx.as_ui_history()).pack(),
            style='danger',
        )
        menu.footer_keyboard.add_row(*buttons)

        parts = []
        if props.first_response.text.value:
            parts.append(
                f'<b><i>{ru("💬 Текст ответа")}:</i></b>'
                f'<blockquote>{html.escape(props.first_response.text.value)}</blockquote>',
            )

        if parts:
            menu.main_text = menu.main_text.strip() + '\n\n' + '\n\n'.join(parts)
        return menu


class GreetingsNodeMenuMod(MenuModification, modification_id='fph:greetings_node_menu_mod'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        node = props.get_node(ctx.entry_path)
        return node.is_child(props.first_response) and isinstance(node, FirstResponseToOfferNode)

    async def modify(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps, hub: FPH) -> Menu:
        node: FirstResponseToOfferNode = props.get_properties(ctx.entry_path)

        await self.modify_header(ctx, menu, hub)
        self.add_remove_button(ctx, menu)
        self.modify_main_text(menu, node)
        return menu

    async def modify_header(self, ctx: NodeMenuContext, menu: Menu, hub: FPH) -> None:
        if not hub.funpay.authenticated:
            return

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

    def add_remove_button(self, ctx: NodeMenuContext, menu: Menu) -> None:
        menu.footer_keyboard.add_row(
            *confirmable_button(
                ctx=ctx,
                button_id='delete_rule',
                text=ru('🗑️ Удалить'),
                callback_data=cbs.RemoveGreetings(
                    offer_id=ctx.entry_path[-1],
                    ui_history=ctx.ui_history,
                ).pack(),
                style='danger',
            ),
        )

    def modify_main_text(self, menu: Menu, node: FirstResponseToOfferNode) -> None:
        parts = []
        if node.text.value:
            parts.append(
                f'<b><i>{ru("💬 Текст приветствия")}:</i></b>'
                f'<blockquote>{html.escape(node.text.value)}</blockquote>',
            )

        if parts:
            menu.main_text = menu.main_text.strip() + '\n\n' + '\n\n'.join(parts)


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
    context_type=MenuContext,
):
    async def build(self, ctx: MenuContext, hub: FPH, properties: FPHProps) -> Menu:
        menu = Menu(finalizer=StripAndNavigationFinalizer())
        menu.main_text = translater.translate(
            '⌨️ Выберите лот, к которому хотите привязать ответ на первое сообщение '
            'или введите <b>ID лота</b>.',
        )
        menu.footer_keyboard.add_callback_button(
            button_id='cancel',
            text=ru('🔘 Отмена'),
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
                    callback_data=cbs.BindGreetings(
                        offer_id=str(offer.id),
                        ui_history=ctx.ui_history,
                    ).pack(),
                )
        return menu
