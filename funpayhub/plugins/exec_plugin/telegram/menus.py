from __future__ import annotations

import html
import math
from typing import TYPE_CHECKING, Any

from aiogram.types import InlineKeyboardButton
from eventry.asyncio.callable_wrappers import CallableWrapper

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, UIContext
from funpayhub.app.telegram.ui.default_builders import default_finalizer

from .callbacks import SendExecFile, ChangeViewPage


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

    first_element = ctx.menu_page * ctx.max_elements_on_page
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
        callback_data=SendExecFile(exec_id=exec_id).pack(),
    )

    return [
        [Button(id='download_exec_files', obj=download_btn)],
        [Button(id='exec_switch_code_output', obj=btn)],
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
        callback_data=SendExecFile(exec_id=exec_id).pack(),
    )

    return [
        [Button(id='download_exec_files', obj=download_btn)],
        [Button(id='exec_switch_code_output', obj=btn)],
    ]


build_code_keyboard = CallableWrapper(build_code_keyboard)


# view navigation
async def build_header(ui: UIRegistry, ctx: UIContext, total_pages: int) -> Keyboard:
    kb = []
    if total_pages < 2:
        return kb

    page = ctx.callback.data.get('show_page', 0)

    page_amount_cb = cbs.Dummy().pack()
    page_amount_btn = InlineKeyboardButton(
        text=f'{page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=join_callbacks(ctx.callback.pack(), page_amount_cb),
    )

    to_first_cb = ChangeViewPage(page=0).pack() if page > 0 else cbs.Dummy().pack()
    to_first_btn = InlineKeyboardButton(
        text='⏪' if page > 0 else '❌',
        callback_data=join_callbacks(ctx.callback.pack(), to_first_cb),
    )

    to_last_cb = (
        ChangeViewPage(page=total_pages - 1).pack()
        if page < total_pages - 1
        else cbs.Dummy().pack()
    )
    to_last_btn = InlineKeyboardButton(
        text='⏩' if page < total_pages - 1 else '❌',
        callback_data=join_callbacks(ctx.callback.pack(), to_last_cb),
    )

    to_previous_cb = ChangeViewPage(page=page - 1).pack() if page > 0 else cbs.Dummy().pack()
    to_previous_btn = InlineKeyboardButton(
        text='◀️' if page > 0 else '❌',
        callback_data=join_callbacks(ctx.callback.pack(), to_previous_cb),
    )

    to_next_cb = (
        ChangeViewPage(page=page + 1).pack() if page < total_pages - 1 else cbs.Dummy().pack()
    )
    to_next_btn = InlineKeyboardButton(
        text='▶️' if page < total_pages - 1 else '❌',
        callback_data=join_callbacks(ctx.callback.pack(), to_next_cb),
    )

    kb.insert(
        0,
        [
            Button(id='to_first_page', obj=to_first_btn),
            Button(id='to_previous_page', obj=to_previous_btn),
            Button(id='page_counter', obj=page_amount_btn),
            Button(id='to_next_page', obj=to_next_btn),
            Button(id='to_last_page', obj=to_last_btn),
        ],
    )

    return kb


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
        finalizer=default_finalizer,
    )


async def exec_output_menu_builder(
    ui: UIRegistry,
    ctx: UIContext,
    exec_registry: ExecutionResultsRegistry,
    data: dict[str, Any],
):
    exec_id = ctx.callback.data['exec_id']
    page = ctx.callback.data.get('show_page', 0)
    result = exec_registry.registry[exec_id]
    total_pages = math.ceil(result.buffer_len / MAX_TEXT_LEN)
    first = page * MAX_TEXT_LEN
    last = first + MAX_TEXT_LEN
    text = '<pre>' + html.escape(result.buffer.getvalue()[first:last]) + '</pre>'
    text = f"""<b><u>Исполнение {exec_id}</u></b>
    
{
        f'✅ Исполнение длилось {result.execution_time} секунд.'
        if not result.error
        else f'❌ Исполнение длилось {result.execution_time} секунд и завершилось ошибкой.'
    }

<b><u>Вывод исполнения:</u></b>
{text}
"""
    return Menu(
        ui=ui,
        context=ctx,
        text=text,
        image=None,
        header_keyboard=await build_header(ui, ctx, total_pages),
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
    page = ctx.callback.data.get('show_page', 0)
    total_pages = math.ceil(result.code_len / MAX_TEXT_LEN)
    first = page * MAX_TEXT_LEN
    last = first + MAX_TEXT_LEN
    text = '<pre>' + result.code[first:last] + '</pre>'

    text = f"""<b><u>Исполнение {exec_id}</u></b>

{
        f'✅ Исполнение длилось {result.execution_time} секунд.'
        if not result.error
        else f'❌ Исполнение длилось {result.execution_time} секунд и завершилось ошибкой.'
    }

<b><u>Код исполнения:</u></b>
{text}
    """
    return Menu(
        ui=ui,
        context=ctx,
        text=text,
        image=None,
        header_keyboard=await build_header(ui, ctx, total_pages),
        footer_keyboard=await build_code_keyboard((ui, ctx), data=data),
        finalizer=default_finalizer,
    )
