from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.lib.telegram.ui import Button, MenuModification
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from .ids import MenuIds


if TYPE_CHECKING:
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
