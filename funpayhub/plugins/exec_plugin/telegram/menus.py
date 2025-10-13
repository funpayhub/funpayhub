from __future__ import annotations

import html
import math
from typing import TYPE_CHECKING, Literal, Final

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.telegram.ui import UIRegistry, PropertiesUIContext
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, UIContext
from funpayhub.app.telegram.ui.premade import default_finalizer_factory
from funpayhub.app.telegram.ui.premade import build_view_navigation_buttons
from .callbacks import SendExecFile


if TYPE_CHECKING:
    from funpayhub.plugins.exec_plugin.types import (
        ExecutionResultsRegistry as ExecRReg,
        ExecutionResult as ExecR
    )


MAX_TEXT_LEN: Final = 3000


# real keyboard
async def exec_list_kb(ctx: UIContext, exec_registry: ExecRReg) -> Keyboard:
    keyboard = []

    for exec_id, result in exec_registry.registry.items():
        keyboard.append([
            Button(
                button_id=f'open_exec_output:{exec_id}',
                text=f'{"❌" if result.error else "✅"} {exec_id}',
                callback_data=cbs.OpenMenu(
                    menu_id='exec_output',
                    data={'exec_id': exec_id},
                    history=ctx.callback.as_history()
                ).pack(),
            )
        ])
    return keyboard


async def exec_view_kb(ctx: UIContext, mode: Literal['output', 'code']) -> Keyboard:
    btn = Button(
        button_id='download_exec_files',
        text='🔲 Код' if mode == 'output' else '📄 Вывод',
        callback_data=cbs.OpenMenu(
            menu_id='exec_code' if mode =='output' else 'exec_output',
            data={'exec_id': ctx.callback.data['exec_id']},
            history=ctx.callback.history
        ).pack()
    )

    download_btn = Button(
        button_id='exec_switch_code_output',
        text='💾 Скачать',
        callback_data=SendExecFile(exec_id=ctx.callback.data['exec_id']).pack(),
    )

    return [[btn], [download_btn]]


async def exec_view_text(ctx: UIContext, result: ExecR, mode: Literal['output', 'code']) -> str:
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
async def exec_list_menu_builder(ui: UIRegistry, ctx: UIContext, exec_registry: ExecRReg) -> Menu:
    return Menu(
        ui=ui,
        context=ctx,
        text='Exec registry',
        image=None,
        header_keyboard=None,
        keyboard=await exec_list_kb(ctx, exec_registry),
        finalizer=default_finalizer_factory(),
    )


async def exec_output_menu_builder(ui: UIRegistry, ctx: UIContext, exec_registry: ExecRReg) -> Menu:
    result = exec_registry.registry[ctx.callback.data['exec_id']]
    total_pages = math.ceil(result.buffer_len / MAX_TEXT_LEN)

    return Menu(
        ui=ui,
        context=ctx,
        text=await exec_view_text(ctx, result, 'output'),
        image=None,
        header_keyboard=await build_view_navigation_buttons(ctx, total_pages),
        keyboard=await exec_view_kb(ctx, 'output'),
        finalizer=default_finalizer_factory(),
    )


async def exec_code_menu_builder(ui: UIRegistry, ctx: UIContext, exec_registry: ExecRReg) -> Menu:
    result = exec_registry.registry[ ctx.callback.data['exec_id']]
    total_pages = math.ceil(result.code_len / MAX_TEXT_LEN)

    return Menu(
        ui=ui,
        context=ctx,
        text=await exec_view_text(ctx, result, 'code'),
        image=None,
        header_keyboard=await build_view_navigation_buttons(ctx, total_pages),
        keyboard=await exec_view_kb(ctx, 'code'),
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