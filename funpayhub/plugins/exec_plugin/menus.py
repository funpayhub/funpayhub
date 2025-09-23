from typing import TYPE_CHECKING

from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.telegram.ui.types import Button, Menu, UIContext, Keyboard
from funpayhub.lib.telegram.ui import UIRegistry
from aiogram.types import InlineKeyboardButton
from funpayhub.lib.telegram.utils import join_callbacks
import funpayhub.plugins.exec_plugin.telegram.callbacks as ecbs
import funpayhub.lib.telegram.callbacks as cbs
import math
from typing import Any
import html

if TYPE_CHECKING:
    from funpayhub.plugins.exec_plugin.types import ExecutionResultsRegistry
    from funpayhub.app.properties import FunPayHubProperties


# helpers
async def build_navigation(
    ui: UIRegistry,
    ctx: UIContext,
    total_pages: int,
) -> Keyboard:
    kb = []

    if ctx.callbacks_history:
        back_btn = InlineKeyboardButton(
            text=ui.translater.translate('$back', ctx.language),
            callback_data=join_callbacks(*ctx.callbacks_history),
        )
        kb = [[Button(id='back', obj=back_btn)]]

    if total_pages < 2:
        return kb

    page_amount_cb = (
        cbs.ChangePageManually(total_pages=total_pages).pack()
        if total_pages > 1
        else cbs.Dummy().pack()
    )
    page_amount_btn = InlineKeyboardButton(
        text=f'{ctx.page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=join_callbacks(*ctx.callbacks_history, ctx.current_callback, page_amount_cb),
    )

    to_first_cb = cbs.ChangePageTo(page=0).pack() if ctx.page > 0 else cbs.Dummy().pack()
    to_first_btn = InlineKeyboardButton(
        text='⏪' if ctx.page > 0 else '❌',
        callback_data=join_callbacks(*ctx.callbacks_history, ctx.current_callback, to_first_cb),
    )

    to_last_cb = (
        cbs.ChangePageTo(page=total_pages - 1).pack()
        if ctx.page < total_pages - 1
        else cbs.Dummy().pack()
    )
    to_last_btn = InlineKeyboardButton(
        text='⏩' if ctx.page < total_pages - 1 else '❌',
        callback_data=join_callbacks(*ctx.callbacks_history, ctx.current_callback, to_last_cb),
    )

    to_previous_cb = (
        cbs.ChangePageTo(page=ctx.page - 1).pack() if ctx.page > 0 else cbs.Dummy().pack()
    )
    to_previous_btn = InlineKeyboardButton(
        text='◀️' if ctx.page > 0 else '❌',
        callback_data=join_callbacks(*ctx.callbacks_history, ctx.current_callback, to_previous_cb),
    )

    to_next_cb = (
        cbs.ChangePageTo(page=ctx.page + 1).pack()
        if ctx.page < total_pages - 1
        else cbs.Dummy().pack()
    )
    to_next_btn = InlineKeyboardButton(
        text='▶️' if ctx.page < total_pages - 1 else '❌',
        callback_data=join_callbacks(*ctx.callbacks_history, ctx.current_callback, to_next_cb),
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
        btn = InlineKeyboardButton(
            text=f'{"❌" if result.error else "✅"} {exec_id}',
            callback_data=join_callbacks(
                *ctx.callbacks_history,
                ctx.current_callback,
                ecbs.OpenExecOutput(exec_id=exec_id, page=ctx.page).pack()
            )
        )
        keyboard.append([Button(id=f'open_exec_output:{exec_id}', obj=btn)])

    return keyboard

build_executions_list_keyboard = CallableWrapper(build_executions_list_keyboard)


async def build_output_keyboard(
    ui: UIRegistry,
    ctx: UIContext,
):
    unpacked = ecbs.OpenExecOutput.unpack(ctx.current_callback)
    btn = InlineKeyboardButton(
        text='Code',
        callback_data=join_callbacks(
        *ctx.callbacks_history,
        ecbs.OpenExecCode(exec_id=unpacked.exec_id).pack()
        )
    )

    return [[Button(id='exec_switch_code_output', obj=btn)]]


async def build_code_keyboard(
    ui: UIRegistry,
    ctx: UIContext,
):
    exec_id = ctx.data['exec_id']

    btn = InlineKeyboardButton(
        text='Code',
        callback_data=join_callbacks(
            *ctx.callbacks_history,
            ecbs.OpenExecCode(exec_id=unpacked.exec_id).pack()
        )
    )

    return [[Button(id='exec_switch_code_output', obj=btn)]]


# menus
async def executions_list_menu(
    ui: UIRegistry,
    ctx: UIContext,
    exec_registry: ExecutionResultsRegistry,
    data: dict[str, Any]
):
    total_pages = math.ceil(len(exec_registry.registry.items()) / ctx.max_elements_on_page)

    return Menu(
        ui=ui,
        context=ctx,
        text='Exec registry',
        image=None,
        upper_keyboard=None,
        keyboard=await build_executions_list_keyboard((ui, ctx), data=data),
        footer_keyboard=await build_navigation(ui=ui, ctx=ctx, total_pages=total_pages),
    )


async def exec_output_menu(
    ui: UIRegistry,
    ctx: UIContext,
    exec_registry: ExecutionResultsRegistry,
):
    unpacked = ecbs.OpenExecOutput.unpack(ctx.current_callback)
    result = exec_registry.registry[unpacked.exec_id]

    total_pages = math.ceil(result.buffer_len / 3000)
    first = ctx.page * 3000
    last = first + 3000
    text = f'<code>' + result.buffer.getvalue()[first:last] + '</code>'

    return Menu(
        ui=ui,
        context=ctx,
        text=text,
        image=None,
        upper_keyboard=None,
        keyboard=None,
        footer_keyboard = await build_navigation(ui, ctx, total_pages=total_pages),
    )


async def exec_code_menu(
    ui: UIRegistry,
    ctx: UIContext,
    exec_registry: ExecutionResultsRegistry,
):
    unpacked = ecbs.OpenExecCode.unpack(ctx.current_callback)
    result = exec_registry.registry[unpacked.exec_id]

    total_pages = math.ceil(result.code_len / 3000)
    first = ctx.page * 3000
    last = first + 3000
    text = f'<code>' + result.code[first:last] + '</code>'

    return Menu(
        ui=ui,
        context=ctx,
        text=text,
        image=None,
        upper_keyboard=None,
        keyboard=None,
        footer_keyboard=await build_navigation(ui, ctx, total_pages=total_pages),
    )