from __future__ import annotations

import time
import textwrap
import contextlib
from typing import Any
from copy import copy

from aiogram import Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaDocument
from aiogram.filters import Command

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui import MenuRenderContext, UIRegistry
from funpayhub.plugins.exec_plugin.types import LockableBuffer, ExecutionResultsRegistry

from .callbacks import SendExecFile


r = Router(name='exec_plugin')


@r.message(Command('execlist'))
async def exec_list_menu(message: Message, tg_ui: UIRegistry, data: dict[str, Any]):
    context = MenuRenderContext(
        menu_id='exec_list',
        trigger=message,
        data={'callback_data': cbs.OpenMenu(menu_id='exec_list')}
    )
    await (await tg_ui.build_menu(context, data)).reply_to(message)


@r.message(Command('exec'))
async def execute_python_code(
    message: Message,
    data: dict[str, Any],
    exec_registry: ExecutionResultsRegistry,
    tg_ui: UIRegistry,
):
    if message.from_user.id != 5991368886:
        return

    split = message.text.split('\n', maxsplit=1)
    if len(split) < 2:
        return
    command = split[0].strip().split(maxsplit=1)
    exec_id = command[1] if len(command) < 1 else None
    source = split[1].strip()

    temp_buffer = LockableBuffer()
    error = False

    a = time.time()
    with contextlib.redirect_stdout(temp_buffer):
        with contextlib.redirect_stderr(temp_buffer):
            try:
                glob = copy(globals())
                glob.update(data, message=message, buffer=temp_buffer)
                code = f'async def __wrapper_function__():\n{textwrap.indent(source, "  ")}'
                _locals = {}
                exec(code, glob, _locals)
                fn = _locals['__wrapper_function__']
                fn.__globals__.update(glob)
                await fn()
            except:
                error = True
                import traceback
                traceback.print_exc()
    execution_time = time.time() - a

    r = exec_registry.add_result(
        id=exec_id,
        code=source,
        error=error,
        buffer=temp_buffer,
        execution_time=execution_time,
    )

    context = MenuRenderContext(
        menu_id='exec_output',
        trigger=message,
        data={
            'callback_data': cbs.OpenMenu(
                menu_id='exec_output',
                history=[cbs.OpenMenu(menu_id='exec_list').pack(hash=False)]
            ),
            'exec_id': r.id
        }
    )

    await (await tg_ui.build_menu(context, data)).reply_to(message)


@r.callback_query(SendExecFile.filter())
async def send_exec_file(
    query: CallbackQuery,
    exec_registry: ExecutionResultsRegistry,
    callback_data: SendExecFile,
):
    result = exec_registry.registry[callback_data.exec_id]
    files = []

    if 0 < result.code_size <= 51380224:
        files.append(
            InputMediaDocument(
                media=BufferedInputFile(result.code.encode(), filename='code.py'),
                caption=f'Код исполнения {result.id}',
            ),
        )
    if 0 < result.buffer_size <= 51380224:
        files.append(
            InputMediaDocument(
                media=BufferedInputFile(result.buffer.getvalue().encode(), filename='output.txt'),
                caption=f'Вывод выполнения {callback_data.exec_id}',
            ),
        )

    if not files:
        await query.answer(text='Размеры файлов слишком большие.', show_alert=True)
        return

    await query.answer(
        text='Выгрузка файлов началась. Это может занять некоторое время.', show_alert=True
    )

    await query.message.answer_media_group(media=files)
