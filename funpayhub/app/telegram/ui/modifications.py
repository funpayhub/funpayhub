from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.app.telegram import callbacks as cbs
from funpayhub.lib.telegram.ui import Button, MenuModification
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from .ids import MenuIds
from .premade import AddRemoveButtonBaseModification


if TYPE_CHECKING:
    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import Menu
    from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext


class PropertiesMenuModification(
    MenuModification,
    modification_id='fph:main_properties_menu_modification',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu) -> bool:
        return ctx.menu_id == MenuIds.props_node and ctx.entry_path == []

    async def modify(self, ctx: NodeMenuContext, menu: Menu, translater: Tr) -> Menu:
        menu.main_keyboard.insert(
            1,
            [
                Button.callback_button(
                    button_id='open_current_chat_notifications',
                    text=translater.translate('$telegram_notifications'),
                    callback_data=OpenMenu(
                        menu_id=MenuIds.tg_chat_notifications,
                        from_callback=ctx.callback_data,
                    ).pack(),
                ),
            ],
        )
        return menu


class AutoDeliveryPropertiesMenuModification(
    MenuModification,
    modification_id='fph:auto_delivery_properties_menu_modification',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu) -> bool:
        return ctx.menu_id == MenuIds.props_node and ctx.entry_path == ['auto_delivery']

    async def modify(self, ctx: NodeMenuContext, menu: Menu, translater: Tr):
        menu.main_keyboard.add_callback_button(
            button_id='open_goods_sources_list',
            text=translater.translate('$goods_sources_list'),
            callback_data=OpenMenu(
                menu_id=MenuIds.goods_sources_list,
                from_callback=ctx.callback_data,
            ).pack(),
        )
        return menu


class AddFormattersListButtonModification(
    MenuModification,
    modification_id='fph:add_formatters_list_button_modification',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu) -> bool:
        if not ctx.entry_path:
            return False

        return any(
            [
                ctx.entry_path[0] == 'auto_response' and ctx.entry_path[-1] == 'response_text',
                ctx.entry_path[0] == 'review_reply' and ctx.entry_path[-1] == 'review_reply_text',
                ctx.entry_path[0] == 'review_reply' and ctx.entry_path[-1] == 'chat_reply_text',
            ],
        )

    async def modify(self, ctx: NodeMenuContext, menu: Menu, translater: Tr) -> Menu:
        if ctx.entry_path[0] == 'auto_response' and ctx.entry_path[-1] == 'response_text':
            query = 'fph:general|fph:message'
        elif any(
            [
                ctx.entry_path[0] == 'review_reply' and ctx.entry_path[-1] == 'review_reply_text',
                ctx.entry_path[0] == 'review_reply' and ctx.entry_path[-1] == 'chat_reply_text',
            ],
        ):
            query = 'fph:general|fph:order'
        else:
            query = None

        menu.footer_keyboard.add_callback_button(
            button_id='open_formatters_list',
            text=translater.translate('$open_formatters_list'),
            callback_data=OpenMenu(
                menu_id=MenuIds.formatters_list,
                new_message=True,
                data={'query': query} if query is not None else {},
            ).pack(),
        )
        return menu


class AddOfferButtonModification(
    MenuModification,
    modification_id='fph:add_offer_button_modification',
):
    """Модификация добавляет кнопку \'Добавить правило\' в меню настроек автовыдачи."""

    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return ctx.entry_path == properties.auto_delivery.path

    async def modify(self, ctx: NodeMenuContext, menu: Menu, translater: Tr) -> Menu:
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

    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == properties.auto_delivery.id

    async def modify(
        self,
        ctx: NodeMenuContext,
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
    async def filter(self, ctx: NodeMenuContext, menu: Menu) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == 'auto_delivery'

    async def modify(self, ctx: NodeMenuContext, menu: Menu, translater: Tr) -> Menu:
        delete_callback = cbs.DeleteAutoDeliveryRule(
            rule=ctx.entry_path[1],
            from_callback=ctx.callback_data,
        ).pack()

        return await self._modify(ctx, menu, translater, delete_callback=delete_callback)
