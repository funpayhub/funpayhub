from __future__ import annotations

import html
import math
from typing import TYPE_CHECKING, Literal, Final

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.telegram.ui import Menu, Button, Keyboard, MenuRenderContext, UIRegistry
from funpayhub.app.telegram.ui.premade import default_finalizer_factory
from funpayhub.app.telegram.ui.premade import build_view_navigation_buttons
from .callbacks import SendExecFile


if TYPE_CHECKING:
    from funpayhub.plugins.exec_plugin.types import (
        ExecutionResultsRegistry as ExecRReg,
        ExecutionResult as ExecR
    )


MAX_TEXT_LEN: Final = 3000


async def exec_view_kb(ctx: MenuRenderContext, mode: Literal['output', 'code']) -> Keyboard:
    callback_data = ctx.callback_data
    btn = Button(
        button_id='download_exec_files',
        obj=InlineKeyboardButton(
            text='🔲 Код' if mode == 'output' else '📄 Вывод',
            callback_data=cbs.OpenMenu(
                menu_id='exec_code' if mode =='output' else 'exec_output',
                data={'exec_id': ctx.data['exec_id']},
                history=callback_data.history if callback_data is not None else []
            ).pack()
        )
    )

    download_btn = Button(
        button_id='exec_switch_code_output',
        obj=InlineKeyboardButton(
            text='💾 Скачать',
            callback_data=SendExecFile(exec_id=ctx.data['exec_id']).pack(),
        )
    )

    return [[btn], [download_btn]]


async def exec_view_text(
    ctx: MenuRenderContext,
    result: ExecR,
    mode: Literal['output', 'code']
) -> str:
    view_text = result.buffer.getvalue() if mode == 'output' else result.code
    first = ctx.view_page * MAX_TEXT_LEN
    last = first + MAX_TEXT_LEN
    text = '<pre>' + html.escape(view_text[first:last]) + '</pre>'
    return f"""<b><u>Исполнение {result.id}</u></b>

{
f'✅ Исполнение длилось {result.execution_time} секунд.'
if not result.error
else 
f'❌ Исполнение длилось {result.execution_time} секунд и завершилось ошибкой.'
}

<b><u>{'Вывод' if mode=='output' else 'Код'} исполнения:</u></b>
{text}"""


# menus
async def exec_list_menu_builder(
    ui: UIRegistry,
    ctx: MenuRenderContext,
    exec_registry: ExecRReg
) -> Menu:
    keyboard = []
    callback_data = ctx.callback_data

    for exec_id, result in exec_registry.registry.items():
        keyboard.append([
            Button(
                button_id=f'open_exec_output:{exec_id}',
                obj=InlineKeyboardButton(
                    text=f'{"❌" if result.error else "✅"} {exec_id}',
                    callback_data=cbs.OpenMenu(
                        menu_id='exec_output',
                        data={'exec_id': exec_id},
                        history=callback_data.as_history() if callback_data is not None else []
                    ).pack(),
                )
            )
        ])

    return Menu(
        text='Exec registry',
        main_keyboard=keyboard,
        finalizer=default_finalizer_factory(),
    )


async def exec_output_menu_builder(
    ui: UIRegistry,
    ctx: MenuRenderContext,
    exec_registry: ExecRReg
) -> Menu:
    result = exec_registry.registry[ctx.data['exec_id']]
    total_pages = math.ceil(result.buffer_len / MAX_TEXT_LEN)

    return Menu(
        text=await exec_view_text(ctx, result, 'output'),
        header_keyboard=await build_view_navigation_buttons(ctx, total_pages),
        main_keyboard=await exec_view_kb(ctx, 'output'),
        finalizer=default_finalizer_factory(),
    )


async def exec_code_menu_builder(ui: UIRegistry, ctx: MenuRenderContext, exec_registry: ExecRReg) -> Menu:
    result = exec_registry.registry[ctx.data['exec_id']]
    total_pages = math.ceil(result.code_len / MAX_TEXT_LEN)

    return Menu(
        text=await exec_view_text(ctx, result, 'code'),
        image=None,
        header_keyboard=await build_view_navigation_buttons(ctx, total_pages),
        main_keyboard=await exec_view_kb(ctx, 'code'),
        finalizer=default_finalizer_factory(),
    )


# Main Menu Modification
async def main_props_menu_modification(
    ui: UIRegistry,
    ctx: PropertiesUIContext,
    menu: Menu
) -> Menu:
    if not isinstance(ctx.entry, FunPayHubProperties):
        return menu

    menu.keyboard.append([
        Button(
            button_id='open_exec_registry',
            text='💻 Exec Registry',
            callback_data=cbs.OpenMenu(menu_id='exec_list', history=[ctx.callback.pack()]).pack()
        )
    ])

    return menu