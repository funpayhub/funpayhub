from __future__ import annotations

from typing import TYPE_CHECKING

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, UIContext
from funpayhub.lib.hub.text_formatters import FormattersRegistry
from ..ids import MenuIds

from .. import premade

if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


# Formatters
async def formatters_list_menu_builder(
    ui: UIRegistry,
    ctx: UIContext,
    fp_formatters: FormattersRegistry,
) -> Menu:
    keyboard = []
    for formatter in fp_formatters:
        keyboard.append([
            Button(
                button_id=f'open_formatter_info:{formatter.key}',
                text=ui.translater.translate(formatter.name, ctx.language),
                callback_data=cbs.OpenMenu(
                    menu_id=MenuIds.FORMATTER_INFO,
                    data={'formatter_id': formatter.key},
                    history=[ctx.callback.pack()]
                ).pack(),
            )
        ])

    return Menu(
        ui=ui,
        context=ctx,
        text='Форматтеры',
        image=None,
        header_keyboard=None,
        keyboard=keyboard,
        finalizer=premade.default_finalizer_factory(),
    )


async def formatter_info_menu_builder(
    ui: UIRegistry,
    ctx: UIContext,
    fp_formatters: FormattersRegistry,
):
    formatter = fp_formatters[ctx.callback.data['formatter_id']]
    text = f"""{ui.translater.translate(formatter.name, ctx.language)}

{ui.translater.translate(formatter.description, ctx.language)}
"""
    return Menu(
        ui=ui,
        context=ctx,
        text=text,
        image=None,
        finalizer=premade.default_finalizer_factory(),
    )
