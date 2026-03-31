from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpayhub.lib.properties import StringParameter
from funpayhub.lib.telegram.ui import Button, MenuModification
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from funpayhub.app.properties.flags import FormattersQueryFlag
from funpayhub.lib.translater import translater

from .ids import MenuIds
from funpayhub.app.properties.review_reply import ReviewReplyPropertiesEntry, ReviewReplyProperties

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


class AddGoodsSourcesBtnToADMod(MenuModification, modification_id='fph:ad_add_goods_sources'):
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


class AddFormattersButtonModification(MenuModification, modification_id='fph:formatters_flag_btn'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        try:
            node = props.get_node(ctx.entry_path)
        except Exception:
            return False

        return isinstance(node, StringParameter) and node.get_flag(FormattersQueryFlag) is not None

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


class AutoDeliveryNodeInfoModification(MenuModification, modification_id='fph:ad_info_mod'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        node = props.get_node(ctx.entry_path)
        return node.is_child(props.auto_delivery) and isinstance(node, AutoDeliveryEntryProperties)

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
                    f'<b><i>{ru('⚠️ Источник товаров')}</i></b>: '
                    f'<code>{html.escape(node.goods_source.value)}</code>\n'
                    f'<b><i>{ru('⚠️ Источник недоступен. Автовыдача не работает!')}</i></b>'
                )
            else:
                parts.append(
                    f'<b><i>{ru('🗳 Источник товаров')}</i></b>: '
                    f'<code>{html.escape(source.display_id)}</code>\n'
                    f'<b><i>{ru('🗳 Доступно товаров')}: <code>{len(source)}</code></i></b>'
                )

        if node.delivery_text.value:
            parts.append(
                f'<b><i>{ru('💬 Текст выдачи')}:</i></b>'
                f'<blockquote>{html.escape(node.delivery_text.value)}</blockquote>'
            )

        menu.main_text = '\n\n'.join(parts)

        return menu


class ReviewResponseModification(MenuModification, modification_id='fph:review_response_mod'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        node = props.get_node(ctx.entry_path)
        return node.is_child(props.review_reply) and isinstance(node, ReviewReplyPropertiesEntry)

    async def modify(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> Menu:
        node: ReviewReplyPropertiesEntry = props.get_properties(ctx.entry_path)

        parts = []

        if node.review_reply_text.value:
            parts.append(
                f'<b><i>{ru('💬 Текст ответа на отзыв')}:</i></b>'
                f'<blockquote>{html.escape(node.review_reply_text.value)}</blockquote>'
            )

        if node.chat_reply_text.value:
            if node.review_reply_text.value:
                parts.append(
                    f'<b><i>{ru('💬 Текст ответа в чат')}:</i></b>'
                    f'<blockquote>{html.escape(node.chat_reply_text.value)}</blockquote>'
                )

        if parts:
            menu.main_text = menu.main_text.strip() + '\n\n' + '\n\n'.join(parts)
        return menu