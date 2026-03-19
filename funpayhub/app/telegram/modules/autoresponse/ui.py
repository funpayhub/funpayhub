from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.lib.telegram.ui import MenuModification

from funpayhub.app.telegram.ui.premade import AddRemoveButtonBaseModification
from funpayhub.lib.translater import translater

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import Menu
    from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


ru = translater.translate


class AddCommandButtonModification(
    MenuModification,
    modification_id='fph:add_command_button_modification',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return ctx.entry_path == properties.auto_response.path

    async def modify(self, ctx: NodeMenuContext, menu: Menu) -> Menu:
        menu.footer_keyboard.add_callback_button(
            button_id='add_command',
            text=ru('➕ Добавить команду'),
            callback_data=cbs.AddCommand(ui_history=ctx.as_ui_history()).pack(),
        )
        return menu


class AddRemoveButtonToCommandModification(
    AddRemoveButtonBaseModification,
    modification_id='fph:add_remove_button_to_command',
):
    async def filter(self, ctx: NodeMenuContext, menu: Menu, properties: FPHProps) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == properties.auto_response.path[0]

    async def modify(self, ctx: NodeMenuContext, menu: Menu) -> Menu:
        return await self._modify(
            ctx,
            menu,
            'delete_ar_rule',
            cbs.RemoveCommand(command=ctx.entry_path[1], ui_history=ctx.as_ui_history()).pack()
        )
