from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpayhub.lib.properties import StringParameter
from funpayhub.lib.telegram.ui import Button, MenuModification
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from funpayhub.app.properties.flags import FormattersQueryFlag
from funpayhub.lib.translater import translater

from .ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import Menu
    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.app.properties.auto_delivery_properties import AutoDeliveryEntryProperties


ru = translater.translate


class PropertiesMenuModification(
    MenuModification,
    modification_id='fph:main_properties_menu_modification',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu) -> bool:
        return ctx.entry_path == []

    async def modify(self, ctx: NodeMenuContext, menu: Menu) -> Menu:
        menu.main_keyboard.insert(
            1,
            Button.callback_button(
                button_id='open_current_chat_notifications',
                text=ru('🔔 Уведомления'),
                callback_data=OpenMenu(
                    menu_id=MenuIds.tg_chat_notifications,
                    ui_history=ctx.as_ui_history(),
                ).pack(),
                row=True,
            ),
        )
        return menu


class AutoDeliveryPropertiesMenuModification(
    MenuModification,
    modification_id='fph:auto_delivery_properties_menu_modification',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        return ctx.entry_path == props.auto_delivery.path

    async def modify(self, ctx: NodeMenuContext, menu: Menu):
        menu.footer_keyboard.add_callback_button(
            button_id='open_goods_sources_list',
            text=ru('🗳 Источники товаров'),
            callback_data=OpenMenu(
                menu_id=MenuIds.goods_sources_list,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )
        return menu


class AddFormattersButtonModification(
    MenuModification,
    modification_id='fph:add_formatters_button',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        if not ctx.entry_path:
            return False

        try:
            node = props.get_node(ctx.entry_path)
        except Exception:
            return False

        if not isinstance(node, StringParameter):
            return False

        r = node.get_flag(FormattersQueryFlag) is not None
        return r

    async def modify(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> Menu:
        node = props.get_node(ctx.entry_path)
        flag = node.get_flag(FormattersQueryFlag)

        menu.footer_keyboard.add_callback_button(
            button_id='open_formatters_list',
            text=ru('🔖 Форматтеры'),
            callback_data=OpenMenu(
                menu_id=MenuIds.formatters_list,
                new_message=True,
                data={'query': flag.query} if flag.query is not None else {},
            ).pack(),
        )

        return menu


class AutoDeliveryNodeInfoModification(
    MenuModification,
    modification_id='fph:auto_delivery_node_info_modification',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == props.auto_delivery.path[0]

    async def modify(
        self,
        ctx: NodeMenuContext,
        menu: Menu,
        props: FPHProps,
        goods_manager: GoodsSourcesManager,
    ) -> Menu:
        node: AutoDeliveryEntryProperties = props.get_properties(ctx.entry_path)
        menu.header_text = '<b><i>' + html.escape(node.id) + '</i></b>'

        parts = []
        if node.goods_source.value:
            source = goods_manager.get(node.goods_source.value)
            if source is None:
                parts.append(
                    '<b><i>'
                    + translater.translate('⚠️ Источник товаров')
                    + '</i></b>'
                    + f': <code>{html.escape(node.goods_source.value)}</code>\n'
                    + '<b><i>'
                    + translater.translate(
                        '⚠️ Источник товаров недоступен. Автовыдача не работает!',
                    )
                    + '</i></b>',
                )
            else:
                parts.append(
                    '<b><i>'
                    + translater.translate('🗳 Источник товаров')
                    + '</i></b>'
                    + f': <code>{html.escape(source.display_id)}</code>\n'
                    + '<b><i>'
                    + translater.translate('🗳 Доступно товаров')
                    + f': <code>{len(source)}</code>'
                    + '</i></b>',
                )

        if node.delivery_text.value:
            parts.append(
                '<b><i>'
                + translater.translate('💬 Текст выдачи')
                + ':</i></b>'
                + '<blockquote>'
                + html.escape(node.delivery_text.value)
                + '</blockquote>',
            )

        menu.main_text = '\n\n'.join(parts)

        return menu
