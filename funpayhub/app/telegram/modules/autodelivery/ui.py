from __future__ import annotations

import html
from typing import TYPE_CHECKING
from itertools import chain

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import (
    Menu,
    Button,
    MenuBuilder,
    MenuContext,
    KeyboardBuilder,
    MenuModification,
)
from funpayhub.lib.base_app.telegram.app.ui.callbacks import ClearState
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext as NodeMenuCtx
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.callbacks import SendMessage
from funpayhub.app.telegram.ui.premade import AddRemoveButtonBaseModification

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpaybotengine.dispatching.events import NewSaleEvent

    from funpayhub.lib.goods_sources import GoodsSourcesManager as GoodsManager

    from funpayhub.app.main import FunPayHub as FPH
    from funpayhub.app.properties import FunPayHubProperties as FPHProps


ru = translater.translate


class NewSaleMenuContext(MenuContext):
    new_sale_event: NewSaleEvent


class AddAutoDeliveryRuleMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.add_auto_delivery_rule,
    context_type=MenuContext,
):
    async def build(self, ctx: MenuContext, hub: FPH) -> Menu:
        menu = Menu(
            main_text=ru('➕ Выберите лот из списка ниже или введите название вручную.'),
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
                        ui_history=ctx.ui_history,
                    ).pack(),
                )

        menu.footer_keyboard.add_callback_button(
            button_id='cancel',
            text=ru('🔘 Отмена'),
            callback_data=ClearState(ui_history=ctx.ui_history).pack(),
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

    async def build(self, ctx: NodeMenuCtx, goods_manager: GoodsManager) -> Menu:
        kb = KeyboardBuilder()
        for source in goods_manager.values():
            kb.add_callback_button(
                button_id=f'bind_goods_source:{source.source_id}',
                text=f'[{len(source)}] {source.display_id}',
                callback_data=cbs.BindGoodsSourceToAutoDelivery(
                    rule=ctx.entry_path[-1],
                    source_id=source.source_id,
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            )

        return Menu(
            main_text=ru('🗳 Выберите источник товаров из списка или введтите название вручную.'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )


class NewSaleNotificationMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.new_sale_notification,
    context_type=NewSaleMenuContext,
):
    async def build(self, ctx: NewSaleMenuContext) -> Menu:
        menu = Menu()

        order = await ctx.new_sale_event.get_order_preview()

        menu.header_text = f'💰 Новый заказ: <b>{html.escape(order.title)}</b>'

        menu.main_text = (
            f'<b><i>👤 Покупатель: <a href="https://funpay.com/users/{order.counterparty.id}/">'
            f'{order.counterparty.username}'
            f'</a></i></b>\n'
            f'<b><i>💵 Сумма:</i></b> <code>{order.total.value} {order.total.character}</code>\n'
            f'<b><i>🆔 ID: <a href="https://funpay.com/orders/{order.id}/">#{order.id}</a></i></b>'
        )

        if delivered_goods := ctx.new_sale_event.data.get('delivered_goods'):
            menu.footer_text = f'<i>📦 Успешно доставлено {len(delivered_goods)} товаров.</i>'
        elif (error := ctx.new_sale_event.data.get('deliver_error')) is not None:
            if isinstance(error, TranslatableException):
                menu.footer_text = (
                    f'<i>❌ Не удалось выдать товары.\n'
                    f'{html.escape(error.format_args(ru(error.message)))}</i>'
                )
            else:
                menu.footer_text = ru('<i>❌ Не удалось выдать товары.\nПодробности в логах.</i>')
        else:
            menu.footer_text = ru(
                '<i>ℹ️ Товары не были выданы, т.к. не было найдено подходящего правила.</i>',
            )

        menu.header_keyboard.add_callback_button(
            button_id='refund',
            text=ru('💸 Вернуть средства'),
            callback_data='dummy',
        )
        menu.header_keyboard.add_callback_button(
            button_id='response',
            text=ru('🗨️ Ответить'),
            callback_data=SendMessage(
                to=ctx.new_sale_event.message.chat_id,
                name=order.counterparty.username,
            ).pack_compact(),
        )

        return menu


class AddOfferButtonModification(
    MenuModification,
    modification_id='fph:add_offer_button_modification',
):
    """Модификация добавляет кнопку \'Добавить правило\' в меню настроек автовыдачи."""

    async def filter(self, ctx: NodeMenuCtx, menu: Menu, properties: FPHProps) -> bool:
        return ctx.entry_path == properties.auto_delivery.path

    async def modify(self, ctx: NodeMenuCtx, menu: Menu) -> Menu:
        btn = Button.callback_button(
            button_id='add_rule',
            text=ru('➕ Добавить правило'),
            callback_data=cbs.OpenAddAutoDeliveryRuleMenu(ui_history=ctx.as_ui_history()).pack(),
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

    async def modify(self, ctx: NodeMenuCtx, menu: Menu) -> Menu:
        entry_path = str([*ctx.entry_path, 'goods_source'])

        for l_index, line in enumerate(menu.main_keyboard):
            for b_index, button in enumerate(line):
                if not button.button_id.endswith(entry_path):
                    continue

                btn = Button.callback_button(
                    button_id='bind_goods_source',
                    text=ru('🗳 Источник товаров'),
                    callback_data=cbs.OpenBindGoodsMenu(
                        rule=ctx.entry_path[-1],
                        ui_history=ctx.as_ui_history(),
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

    async def modify(self, ctx: NodeMenuCtx, menu: Menu) -> Menu:
        delete_callback = cbs.DeleteAutoDeliveryRule(
            rule=ctx.entry_path[1],
            ui_history=ctx.as_ui_history(),
        ).pack()

        return await self._modify(ctx, menu, 'delete_ad_rule', delete_callback=delete_callback)
