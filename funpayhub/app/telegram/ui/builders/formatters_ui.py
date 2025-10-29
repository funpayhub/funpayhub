from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.app.telegram.ui import premade
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuContext, MenuBuilder
from funpayhub.lib.hub.text_formatters import FormattersRegistry

from ..ids import MenuIds


if TYPE_CHECKING:
    pass


# Formatters
class FormatterListMenuBuilder(MenuBuilder):
    id = MenuIds.formatters_list
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        fp_formatters: FormattersRegistry,
        translater: Translater,
    ) -> Menu:
        keyboard = []
        callback_data = ctx.callback_data

        for formatter in fp_formatters:
            keyboard.append(
                [
                    Button(
                        button_id=f'open_formatter_info:{formatter.key}',
                        obj=InlineKeyboardButton(
                            text=translater.translate(formatter.name),
                            callback_data=cbs.OpenMenu(
                                menu_id=MenuIds.formatter_info,
                                data={'formatter_id': formatter.key},
                                history=callback_data.as_history()
                                if callback_data is not None
                                else [],
                            ).pack(),
                        ),
                    ),
                ],
            )

        return Menu(
            text='Форматтеры',
            main_keyboard=keyboard,
            finalizer=premade.default_finalizer_factory(),
        )


class FormatterInfoMenuBuilder(MenuBuilder):
    id = MenuIds.formatter_info
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        fp_formatters: FormattersRegistry,
        translater: Translater,
    ) -> Menu:
        formatter = fp_formatters[ctx.data['formatter_id']]
        text = f"""{translater.translate(formatter.name)}
    
{translater.translate(formatter.description)}
"""
        return Menu(
            text=text,
            finalizer=premade.default_finalizer_factory(),
        )
