from __future__ import annotations

import os
import json
import time
import textwrap
import traceback
import contextlib
from typing import Any
from io import StringIO
from copy import copy

from aiogram import Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaDocument
from aiogram.filters import Command

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui import UIRegistry, MenuContext
from exec_plugin.src.types import ExecutionResult, ExecutionResultsRegistry

from .callbacks import SaveExecCode, SendExecFile


r = Router(name='exec_plugin')


async def execute_code(
    registry: ExecutionResultsRegistry,
    exec_id: str | None,
    code: str,
    execution_dict: dict[str, Any],
) -> ExecutionResult:
    temp_buffer = StringIO()
    error = False

    a = time.time()
    with contextlib.redirect_stdout(temp_buffer):
        with contextlib.redirect_stderr(temp_buffer):
            try:
                glob = copy(globals())
                glob.update(execution_dict)
                # glob.update(data, message=message, buffer=temp_buffer)
                wrapped_code = f'async def __wrapper_function__():\n{textwrap.indent(code, "  ")}'
                _locals: dict[str, Any] = {}
                exec(wrapped_code, glob, _locals)
                fn = _locals['__wrapper_function__']
                fn.__globals__.update(glob)
                await fn()
            except:
                error = True
                traceback.print_exc()
    execution_time = time.time() - a

    return registry.add_result(
        id=exec_id,
        code=code,
        output=temp_buffer.getvalue(),
        error=error,
        execution_time=execution_time,
    )


@r.message(Command('execlist'))
async def exec_list_menu(message: Message, tg_ui: UIRegistry, data: dict[str, Any]):
    context = MenuContext(
        menu_id='exec_list',
        trigger=message,
        data={'callback_data': cbs.OpenMenu(menu_id='exec_list')},
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
    command = split[0].strip().split(maxsplit=1)
    exec_id = command[1] if len(command) > 1 else None
    source = split[1].strip() if len(split) > 1 else None

    if not exec_id and not source:
        await message.answer(
            'Укажите ID исполнения на одной строке с /exec или код исполнения с новой строки.',
        )
        return
    if exec_id and not source:
        if exec_id not in exec_registry.registry:
            await message.answer(f'Исполнение {exec_id!r} не найдено.')
            return
        source = exec_registry.registry[exec_id].code
        exec_id = None

    data = data | {'message': message}
    r = await execute_code(exec_registry, exec_id, source, data)

    context = MenuContext(
        menu_id='exec_output',
        trigger=message,
        data={
            'callback_data': cbs.OpenMenu(
                menu_id='exec_output',
                data={'exec_id': r.id},
                history=[cbs.OpenMenu(menu_id='exec_list').pack(hash=False)],
            ),
            'exec_id': r.id,
        },
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
    if 0 < result.output_size <= 51380224:
        files.append(
            InputMediaDocument(
                media=BufferedInputFile(result.output.encode(), filename='output.txt'),
                caption=f'Вывод выполнения {callback_data.exec_id}',
            ),
        )

    if not files:
        await query.answer(text='Размеры файлов слишком большие.', show_alert=True)
        return

    await query.answer(
        text='Выгрузка файлов началась. Это может занять некоторое время.',
        show_alert=True,
    )

    await query.message.answer_media_group(media=files)


@r.callback_query(SaveExecCode.filter())
async def save_exec(
    query: CallbackQuery,
    exec_registry: ExecutionResultsRegistry,
    callback_data: SaveExecCode,
):
    result = exec_registry.registry[callback_data.exec_id]
    os.makedirs(f'.exec/{callback_data.exec_id}', exist_ok=True)
    with open(f'.exec/{callback_data.exec_id}/exec.json', 'w', encoding='utf-8') as f:
        f.write(
            json.dumps(
                {
                    'code': result.code,
                    'output': result.output,
                    'error': result.error,
                    'execution_time': result.execution_time,
                },
                ensure_ascii=False,
            ),
        )

    await query.answer(f'Данные исполнения сохранены в .exec/{callback_data.exec_id}/exec.json.')
