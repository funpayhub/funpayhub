from __future__ import annotations

from typing import Any

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.telegram.ui import UIContext, UIRegistry
from funpayhub.lib.telegram.callbacks_parsing import add_callback_params, UnpackedCallback, unpack_callback
from funpayhub.plugins.exec_plugin.types import LockableBuffer, ExecutionResultsRegistry
from .callbacks import SendExecFile, ChangeViewPage
import contextlib
from copy import copy
import textwrap
import time
from aiogram.types import BufferedInputFile, InputMediaDocument, Update
from aiogram import Bot, Dispatcher


r = Router(name='exec_plugin')


@r.message(Command('execlist'))
async def exec_list_menu(
    message: Message,
    tg_ui: UIRegistry,
    properties: FunPayHubProperties,
    data: dict[str, Any],
):
    callback_str = cbs.OpenMenu(menu_id='exec_list').pack()
    unpacked = UnpackedCallback(
        current_callback=callback_str,
        history=[],
        data={}
    )

    context = UIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=0,
        callback=unpacked
    )

    menu = await tg_ui.build_menu('exec_list', context, data)

    await message.answer(
        text=menu.text,
        reply_markup=menu.total_keyboard(convert=True, hash=True),
    )


@r.message(Command('exec'))
async def execute_python_code(
    message: Message,
    data: dict[str, Any],
    exec_registry: ExecutionResultsRegistry,
    tg_ui: UIRegistry,
    properties: FunPayHubProperties,
):
    if message.from_user.id != 5991368886:
        return

    split = message.text.split()
    if len(split) < 2:
        return

    if split[1].startswith('<') and split[1].endswith('>'):
        exec_id = split[1][1:-1]
        source = message.text.split(None, 2)[2]
    else:
        exec_id = None
        source = message.text.split(None, 1)[1]

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
        execution_time=execution_time
    )

    callback = cbs.OpenMenu(menu_id='exec_output').pack()

    unpacked_callback = UnpackedCallback(
        current_callback=callback,
        history=[cbs.OpenMenu(menu_id='exec_list').pack()],
        data={'exec_id': r.id}
    )

    context = UIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=0,
        callback=unpacked_callback
    )

    menu = await tg_ui.build_menu('exec_output', context, data)
    await message.answer(
        text=menu.text,
        reply_markup=menu.total_keyboard(convert=True, hash=True),
    )


@r.callback_query(SendExecFile.filter())
async def send_exec_file(
    query: CallbackQuery,
    exec_registry: ExecutionResultsRegistry
):
    unpacked = SendExecFile.unpack(query.data)

    result = exec_registry.registry[unpacked.exec_id]

    files = []

    if result.code_size <= 51380224:
        file = BufferedInputFile(
                result.code.encode('utf-8'),
                filename='code.txt'
            )
        files.append(
            InputMediaDocument(
                media=file,
                caption=f'Код выполнения {unpacked.exec_id}',
            )
        )
    if result.buffer_size <= 51380224:
        file = BufferedInputFile(
            result.buffer.getvalue().encode('utf-8'),
            filename='output.txt'
        )
        files.append(
            InputMediaDocument(
                media=file,
                caption=f'Вывод выполнения {unpacked.exec_id}',
            )
        )

    if not files:
        await query.answer(text='Размеры файлов слишком большие.', show_alert=True)
        return

    await query.answer(text='Выгрузка файлов началась. Это может занять некоторое время.', show_alert=True)

    await query.message.answer_media_group(
        media=files
    )


@r.callback_query(ChangeViewPage.filter())
async def change_view_page(
    query: CallbackQuery,
    unpacked_callback: UnpackedCallback,
    dispatcher: Dispatcher,
    bot: Bot
):
    unpacked = ChangeViewPage.unpack(query.data)

    previous = unpack_callback(unpacked_callback.history[-1])
    previous.data['show_page'] = unpacked.page

    new_query = query.model_copy(update={'data': previous.pack()})

    await dispatcher.feed_update(
        bot,
        Update(
            update_id=-1,
            callback_query=new_query,
        )
    )