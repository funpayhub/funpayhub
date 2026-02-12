from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpayhub.lib.telegram.ui import Button, MenuModification
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from .ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import Menu
    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.app.properties.auto_delivery_properties import AutoDeliveryEntryProperties


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
                    text=translater.translate('🔔 Уведомления'),
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
            text=translater.translate('🗳 Источники товаров'),
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
            text=translater.translate('🔖 Форматтеры'),
            callback_data=OpenMenu(
                menu_id=MenuIds.formatters_list,
                new_message=True,
                data={'query': query} if query is not None else {},
            ).pack(),
        )
        return menu


class AutoDeliveryNodeInfoModification(
    MenuModification,
    modification_id='fph:auto_delivery_node_info_modification',
):
    async def modify(
        self,
        ctx: NodeMenuContext,
        menu: Menu,
        translater: Tr,
        properties: FPHProps,
        goods_manager: GoodsSourcesManager,
    ) -> Menu:
        node: AutoDeliveryEntryProperties = properties.get_properties(ctx.entry_path)
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
                        '⚠️ Источник товаров недоступен. Автовыдача не работает!'
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

    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == properties.auto_delivery.path[0]
