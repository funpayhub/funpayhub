from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import MenuModification

from funpayhub.app.telegram.ui.premade import AddRemoveButtonBaseModification
from funpayhub.app.properties.auto_response import AutoResponseEntryProperties

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import Menu
    from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


ru = translater.translate


class AddCommandBtnMod(MenuModification, modification_id='fph:add_command_btn'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        return ctx.entry_path == props.auto_response.path

    async def modify(self, ctx: NodeMenuContext, menu: Menu) -> Menu:
        menu.footer_keyboard.add_callback_button(
            button_id='add_command',
            text=ru('➕ Добавить команду'),
            callback_data=cbs.AddCommand(ui_history=ctx.as_ui_history()).pack(),
        )
        return menu


class RemoveCmdBtn(AddRemoveButtonBaseModification, modification_id='fph:remove_cmd_btn'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == props.auto_response.path[0]

    async def modify(self, ctx: NodeMenuContext, menu: Menu) -> Menu:
        return await self._modify(
            ctx,
            menu,
            'delete_ar_rule',
            cbs.RemoveCommand(command=ctx.entry_path[1], ui_history=ctx.as_ui_history()).pack(),
        )


class CommandMenuMod(MenuModification, modification_id='fph:command_menu_mod'):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> bool:
        node = props.get_node(ctx.entry_path)
        return node.is_child(props.auto_response) and isinstance(node, AutoResponseEntryProperties)

    async def modify(self, ctx: NodeMenuContext, menu: Menu, props: FPHProps) -> Menu:
        node: AutoResponseEntryProperties = props.get_properties(ctx.entry_path)

        parts = []
        if node.response_text.value:
            parts.append(
                f'<b><i>{ru("💬 Текст ответа")}:</i></b>'
                f'<blockquote>{html.escape(node.response_text.value)}</blockquote>',
            )

        if parts:
            menu.main_text = menu.main_text.strip() + '\n\n' + '\n\n'.join(parts)
        return menu
