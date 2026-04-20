from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.lib.telegram.ui import MenuModification

from . import callbacks as cbs
from ...ui.premade import confirmable_button


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import Menu
    from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


class AddBlockUserButton(MenuModification, modification_id='fph:add_user_to_blocklist_btn'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        return ctx.entry_path == props.black_list.path

    async def modify(self, ctx: NodeMenuContext, menu: Menu) -> Menu:
        menu.footer_keyboard.add_callback_button(
            button_id='block_user',
            text='➕ Добавить пользователя',
            callback_data=cbs.BlockUser(ui_history=ctx.as_ui_history()).pack(),
        )
        return menu


class AddRemoveUserButton(MenuModification, modification_id='fph:remove_user_from_blocklist_btn'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        from funpayhub.app.properties.blacklist import BlackListNode

        node = props.get_node(ctx.entry_path)
        return node.is_child(props.black_list) and isinstance(node, BlackListNode)

    async def modify(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> Menu:
        node = props.get_node(ctx.entry_path)
        from funpayhub.app.properties.blacklist import BlackListNode

        if not isinstance(node, BlackListNode):
            return menu

        menu.footer_keyboard.add_row(
            *confirmable_button(
                button_id='delete_user',
                ctx=ctx,
                text='🗑️ Удалить',
                callback_data=cbs.DeleteUser(
                    ui_history=ctx.ui_history, username=node.username
                ).pack(),
                style='danger',
            ),
        )
        return menu
