from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.app.telegram.ui import premade
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, MenuContext
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

        for formatter in fp_formatters._formatters.values():
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
            finalizer=premade.StripAndNavigationFinalizer(),
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
        formatter = fp_formatters._formatters[ctx.data['formatter_id']]
        categories = fp_formatters._formatters_to_categories[formatter]
        categories_text = '; '.join(translater.translate(i.name) for i in categories)

        text = f"""{translater.translate(formatter.name)}

{translater.translate('$formatters:categories')}: <i>{categories_text}.</i>

{translater.translate(formatter.description)}
"""
        return Menu(
            text=text,
            finalizer=premade.StripAndNavigationFinalizer(),
        )
