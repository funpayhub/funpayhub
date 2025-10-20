from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.app.telegram.ui import premade
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContext
from funpayhub.lib.hub.text_formatters import FormattersRegistry

from ..ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


# Formatters
async def formatters_list_menu_builder(
    ctx: MenuContext,
    fp_formatters: FormattersRegistry,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Menu:
    keyboard = []
    language = properties.general.language.real_value
    callback_data = ctx.callback_data

    for formatter in fp_formatters:
        keyboard.append(
            [
                Button(
                    button_id=f'open_formatter_info:{formatter.key}',
                    obj=InlineKeyboardButton(
                        text=translater.translate(formatter.name, language),
                        callback_data=cbs.OpenMenu(
                            menu_id=MenuIds.formatter_info,
                            data={'formatter_id': formatter.key},
                            history=callback_data.as_history()
                            if callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ]
        )

    return Menu(
        text='Форматтеры',
        main_keyboard=keyboard,
        finalizer=premade.default_finalizer_factory(),
    )


async def formatter_info_menu_builder(
    ctx: MenuContext,
    fp_formatters: FormattersRegistry,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Menu:
    language = properties.general.language.real_value

    formatter = fp_formatters[ctx.data['formatter_id']]
    text = f"""{translater.translate(formatter.name, language)}

{translater.translate(formatter.description, language)}
"""
    return Menu(
        text=text,
        finalizer=premade.default_finalizer_factory(),
    )
