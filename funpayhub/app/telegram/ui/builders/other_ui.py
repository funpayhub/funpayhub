from __future__ import annotations

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import KeyboardBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, MenuContext


class AddCommandMenuBuilder(MenuBuilder):
    id = MenuIds.add_command
    context_type = MenuContext

    async def build(self, ctx: MenuContext, translater: Translater) -> Menu:
        return Menu(
            text='$add_command_message',
            footer_keyboard=KeyboardBuilder(
                keyboard=[
                    Button.callback_button(
                        button_id='clear_state',
                        text=translater.translate('$clear_state'),
                        callback_data=cbs.Clear(
                            delete_message=False,
                            open_previous=True,
                            history=ctx.callback_data.history
                            if ctx.callback_data is not None
                            else [],
                        ).pack(),
                        row=True,
                    ),
                ]
            ),
        )
