from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from aiogram.types import InlineKeyboardButton
from eventry.asyncio.callable_wrappers import CallableWrapper

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.lib.telegram.callbacks_parsing import join_callbacks, add_callback_params
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, UIContext
from .callbacks import SendExecFile
from funpayhub.app.telegram.ui.default_builders import default_finalizer
import html


if TYPE_CHECKING:
    from funpayhub.plugins.exec_plugin.types import ExecutionResultsRegistry


MAX_TEXT_LEN = 3000


# real keyboard
async def build_executions_list_keyboard(
    ui: UIRegistry,
    ctx: UIContext,
    exec_registry: ExecutionResultsRegistry,
) -> Keyboard:
    keyboard = []

    first_element = ctx.page * ctx.max_elements_on_page
    last_element = first_element + ctx.max_elements_on_page
    entries = list(exec_registry.registry.items())[first_element:last_element]

    for exec_id, result in entries:
        callback = cbs.OpenMenu(menu_id='exec_output').pack()
        callback = add_callback_params(callback, exec_id=exec_id)

        btn = InlineKeyboardButton(
            text=f'{"❌" if result.error else "✅"} {exec_id}',
            callback_data=join_callbacks(ctx.callback.pack(), callback),
        )
        keyboard.append([Button(id=f'open_exec_output:{exec_id}', obj=btn)])

    return keyboard


build_executions_list_keyboard = CallableWrapper(build_executions_list_keyboard)


async def build_output_keyboard(
    ui: UIRegistry,
    ctx: UIContext,
):
    exec_id = ctx.callback.data['exec_id']

    callback = cbs.OpenMenu(menu_id='exec_code').pack()
    callback = add_callback_params(callback, exec_id=exec_id)

    btn = InlineKeyboardButton(
        text='🔲 Код',
        callback_data=join_callbacks(
            *ctx.callback.history,
            callback,
        ),
    )

    download_btn = InlineKeyboardButton(
        text='💾 Скачать',
        callback_data=SendExecFile(exec_id=exec_id).pack()
    )

    return [
        [Button(id='download_exec_files', obj=download_btn)],
        [Button(id='exec_switch_code_output', obj=btn)]
    ]
build_output_keyboard = CallableWrapper(build_output_keyboard)

async def build_code_keyboard(
    ui: UIRegistry,
    ctx: UIContext,
):
    exec_id = ctx.callback.data['exec_id']

    callback = cbs.OpenMenu(menu_id='exec_output').pack()
    callback = add_callback_params(callback, exec_id=exec_id)

    btn = InlineKeyboardButton(
        text='📄 Вывод',
        callback_data=join_callbacks(
            *ctx.callback.history,
            callback,
        ),
    )
    download_btn = InlineKeyboardButton(
        text='💾 Скачать',
        callback_data=SendExecFile(exec_id=exec_id).pack()
    )

    return [
        [Button(id='download_exec_files', obj=download_btn)],
        [Button(id='exec_switch_code_output', obj=btn)]
    ]
build_code_keyboard = CallableWrapper(build_code_keyboard)

# menus
async def exec_list_menu_builder(
    ui: UIRegistry,
    ctx: UIContext,
    exec_registry: ExecutionResultsRegistry,
    data: dict[str, Any],
):
    return Menu(
        ui=ui,
        context=ctx,
        text='Exec registry',
        image=None,
        header_keyboard=None,
        footer_keyboard=await build_executions_list_keyboard((ui, ctx), data=data),
        finalizer=default_finalizer
    )


async def exec_output_menu_builder(
    ui: UIRegistry,
    ctx: UIContext,
    exec_registry: ExecutionResultsRegistry,
    data: dict[str, Any],
):
    exec_id = ctx.callback.data['exec_id']
    result = exec_registry.registry[exec_id]
    first = ctx.page * MAX_TEXT_LEN
    last = first + MAX_TEXT_LEN
    text = '<pre>' + html.escape(result.buffer.getvalue()[first:last]) + '</pre>'
    text = f'''<b><u>Исполнение {exec_id}</u></b>
    
{f'✅ Исполнение длилось {result.execution_time} секунд.' if not result.error 
    else f'❌ Исполнение длилось {result.execution_time} секунд и завершилось ошибкой.'}

<b><u>Вывод исполнения:</u></b>
{text}
'''

    return Menu(
        ui=ui,
        context=ctx,
        text=text,
        image=None,
        header_keyboard=None,
        footer_keyboard=await build_output_keyboard((ui, ctx), data=data),
        finalizer=default_finalizer,
    )


async def exec_code_menu_builder(
    ui: UIRegistry,
    ctx: UIContext,
    exec_registry: ExecutionResultsRegistry,
    data: dict[str, Any],
):
    exec_id = ctx.callback.data['exec_id']
    result = exec_registry.registry[exec_id]
    first = ctx.page * MAX_TEXT_LEN
    last = first + MAX_TEXT_LEN
    text = '<pre>' + result.code[first:last] + '</pre>'

    text = f'''<b><u>Исполнение {exec_id}</u></b>

{f'✅ Исполнение длилось {result.execution_time} секунд.' if not result.error
else f'❌ Исполнение длилось {result.execution_time} секунд и завершилось ошибкой.'}

<b><u>Код исполнения:</u></b>
{text}
    '''

    return Menu(
        ui=ui,
        context=ctx,
        text=text,
        image=None,
        header_keyboard=None,
        footer_keyboard=await build_code_keyboard((ui, ctx), data=data),
        finalizer=default_finalizer,
    )
