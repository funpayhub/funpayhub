from __future__ import annotations

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContext


async def add_command_menu_builder(
    ctx: MenuContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Menu:
    language = properties.general.language.real_value

    return Menu(
        text='$add_command_message',
        footer_keyboard=[
            [
                Button(
                    button_id='clear_state',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$clear_state', language),
                        callback_data=cbs.Clear(
                            delete_message=False,
                            open_previous=True,
                            history=ctx.callback_data.history
                            if ctx.callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ],
        ],
    )
