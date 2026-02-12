from __future__ import annotations

import re
import html
from typing import TYPE_CHECKING, Any
from io import BytesIO
from pathlib import Path

from aiogram import Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest

from funpayhub.lib.translater import _
from funpayhub.lib.goods_sources import GoodsSource, FileGoodsSource
from funpayhub.lib.base_app.telegram import utils
from funpayhub.lib.telegram.callback_data import join_callbacks
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from funpayhub.app.workflow_data import get_wfd
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import StateUIContext

from . import (
    states,
    callbacks as cbs,
)
from .ui import GoodsInfoMenuContext


if TYPE_CHECKING:
    from aiogram import Bot as TGBot
    from aiogram.fsm.context import FSMContext

    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import UIRegistry as UI
    from funpayhub.lib.goods_sources import GoodsSourcesManager

    from funpayhub.app.telegram.main import Telegram


r = router = Router(name='fph:goods')


# -------- Helpers --------
async def _set_state_and_send_state_ui(
    query: CallbackQuery,
    callback_data: Any,
    state: Any,
    state_cls: Any,
    text: str,
) -> None:
    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        delete_on_clear=True,
        text=text,
        trigger=query,
    ).build_and_answer(get_wfd().tg_ui_registry, query.message)

    await state_cls(
        source_id=callback_data.source_id,
        message=msg,
        callback_data=callback_data,
    ).set(state)
    await query.answer()


async def _generate_and_send_new_goods_info(
    trigger: CallbackQuery | Message,
    source: GoodsSource,
    callback_data,
) -> None:
    context = GoodsInfoMenuContext(
        menu_id=MenuIds.goods_source_info,
        source_id=source.source_id,
        trigger=trigger,
        callback_override=callback_data.copy_history(
            OpenMenu(
                menu_id=MenuIds.goods_source_info,
                context_data={'source_id': source.source_id},
            ),
        ),
    )

    if isinstance(trigger, Message):
        await context.build_and_answer(get_wfd().tg_ui_registry, trigger)
    elif isinstance(trigger, CallbackQuery):
        await context.build_and_apply(get_wfd().tg_ui_registry, trigger.message)


async def _get_source(trigger: CallbackQuery | Message, source_id: str) -> GoodsSource | None:
    source = get_wfd().goods_manager.get(source_id)
    if source is None:
        text = get_wfd().translater.translate('❌ Источник товаров %s не найден.')
        if isinstance(trigger, CallbackQuery):
            await trigger.answer(text, show_alert=True)
        elif isinstance(trigger, Message):
            await trigger.reply(text)
        return None
    return source


async def _get_data_clear_state(state: FSMContext, clear: bool = True, delete: bool = True) -> Any:
    data = (await state.get_data())['data']
    if clear:
        await state.clear()
    if delete:
        await data.message.delete()
    return data


async def _get_goods_from_message(message: Message) -> list[str]:
    if message.document:
        io = BytesIO()
        file = await message.bot.get_file(message.document.file_id)
        await message.bot.download_file(file.file_path, io)
        return io.getbuffer().tobytes().decode('utf-8').splitlines()
    return message.text.split('\n')


# -------- Handlers --------
@router.callback_query(cbs.DownloadGoods.filter())
async def download_goods(query: CallbackQuery, callback_data: cbs.DownloadGoods) -> None:
    if (source := await _get_source(query, callback_data.source_id)) is None:
        return

    goods = await source.get_goods(-1)

    await query.message.answer_document(
        BufferedInputFile('\n'.join(goods).encode('utf-8'), 'goods.txt'),
        caption=f'<b>{html.escape(source.display_id)}</b>',
    )
    await query.answer()


@router.callback_query(cbs.ReloadGoodsSource.filter())
async def reload_goods(
    query: CallbackQuery,
    callback_data: cbs.ReloadGoodsSource,
    tg: Telegram,
) -> None:
    if (await _get_source(query, callback_data.source_id)) is None:
        await query.answer()
        return

    try:
        await query.answer()
        await tg.fake_query(callback_data, query, pack_history=True)
    except TelegramBadRequest:
        pass


@router.callback_query(cbs.UploadGoods.filter())
@router.callback_query(cbs.RemoveGoods.filter())
@router.callback_query(cbs.AddGoods.filter())
async def upload_goods_set_state(
    query: CallbackQuery,
    translater: Tr,
    state: FSMContext,
    callback_data: cbs.UploadGoods | cbs.RemoveGoods | cbs.AddGoods,
) -> None:
    mapping = {
        cbs.UploadGoods: (
            _(
                '📤 Отправьте список товаров или файл с товарами (каждый товар с новой строки).\n\n'
                '⚠️ Важно: это <b><u>перезапишет</u></b> текущие товары, а не добавит новые.\n'
                'Если вы хотите добавить новые товары к существующим, '
                'используйте кнопку <i>Добавить товары</i>.',
            ),
            states.UploadingGoods,
        ),
        cbs.RemoveGoods: (
            _(
                '🗑️ Укажите номер товара или диапазон для удаления. '
                'Например: <code>1</code> или <code>1-7</code>.\n\n'
                '⚠️ Будьте внимательны: выбранные товары будут удалены '
                'без возможности восстановления.',
            ),
            states.RemovingGoods,
        ),
        cbs.AddGoods: (
            _(
                '➕ Пришлите список товаров или файл с товарами, '
                'где каждая новая строка — отдельный товар.\n\n'
                '⚠️ Важно: новые товары будут <b><u>добавлены</u></b> к текущему списку, '
                'а не перезапишут его.\n'
                'Чтобы заменить весь список, используйте кнопку <i>Выгрузить товары</i>.',
            ),
            states.AddingGoods,
        ),
    }

    text, state_cls = mapping[type(callback_data)]
    text = translater.translate(text)

    await _set_state_and_send_state_ui(query, callback_data, state, state_cls, text)


@router.message(StateFilter(states.UploadingGoods.identifier))
@router.message(StateFilter(states.AddingGoods.identifier))
async def upload_goods(message: Message, state: FSMContext, translater: Tr) -> None:
    data: states.UploadingGoods = await _get_data_clear_state(state)
    if (source := await _get_source(message, data.source_id)) is None:
        return

    try:
        new_goods = await _get_goods_from_message(message)
    except:
        await message.reply(
            translater.translate(
                '❌ Не удалось получить товары из сообщения или файла. Проверьте корректность данных. Подробности в логах.',
            ),
        )
        return

    if isinstance(data, states.UploadingGoods):
        await source.set_goods(new_goods)
    elif isinstance(data, states.AddingGoods):
        await source.add_goods(new_goods)

    await _generate_and_send_new_goods_info(message, source, data.callback_data)


amount_re = re.compile(r'(\d+)-(\d+)')


@router.message(StateFilter(states.RemovingGoods.identifier))
async def remove_goods(message: Message, state: FSMContext, translater: Tr) -> None:
    data = await states.RemovingGoods.get(state)
    if (source := await _get_source(message, data.source_id)) is None:
        await _get_data_clear_state(state)
        return

    start_index, amount = None, None
    text = message.text.replace(' ', '')
    if text.isnumeric():
        start_index, amount = int(text) - 1, 1
    elif amount_re.fullmatch(text):
        start_index, end_index = (int(i) - 1 for i in text.split('-'))
        if end_index > start_index:
            amount = end_index - start_index + 1

    if start_index is None or amount is None or start_index < 0:
        await message.reply(
            translater.translate(
                '❌ Неверный формат ввода. Укажите номер товара или диапазон через дефис, например: <code>1</code> или <code>1-7</code>.',
            ),
        )
        return

    await _get_data_clear_state(state)
    await source.remove_goods(start_index, amount)
    await _generate_and_send_new_goods_info(message, source, data.callback_data)


@router.callback_query(cbs.AddGoodsTxtSource.filter())
async def set_adding_txt_source_state(
    query: CallbackQuery,
    translater: Tr,
    state: FSMContext,
    tg_ui: UI,
    callback_data: cbs.AddGoodsTxtSource,
) -> None:
    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        delete_on_clear=True,
        text=translater.translate(
            '📄 Отправьте название файла или сам файл. Если вы пришлете файл, будет использовать его имя.',
        ),
        trigger=query,
    ).build_and_answer(tg_ui, query.message)

    await states.AddingGoodsTxtSource(message=msg, callback_data=callback_data).set(state)
    await query.answer()


INVALID_CHARS = set('<>:"/\\|?*\0')


@router.message(StateFilter(states.AddingGoodsTxtSource.identifier))
async def add_goods_txt_source(
    msg: Message,
    translater: Tr,
    state: FSMContext,
    tg_ui: UI,
    tg_bot: TGBot,
    goods_manager: GoodsSourcesManager,
) -> None:
    data = await states.AddingGoodsTxtSource.get(state)
    filename = msg.text if msg.text else msg.document.file_name if msg.document else ''

    if not filename:
        await msg.reply(translater.translate('❌ Имя файла не может быть пустым.'))
        return

    if (
        filename in ['.', '..']
        or filename.endswith((' ', '.'))
        or any(c in INVALID_CHARS for c in filename)
        or any(ord(c) < 32 for c in filename)
    ):
        await msg.reply(translater.translate('❌ Невалидное имя файла.'))
        return

    path = Path('storage/goods') / filename
    if not path.suffix == '.txt':
        path = path.with_suffix('.txt')
    new_id = 'file://' + str(path)

    if new_id in goods_manager:
        await msg.reply(translater.translate('❌ Файл %s уже существует.'))
        return

    await state.clear()

    if msg.document:
        file = await tg_bot.get_file(msg.document.file_id)
        buffer = BytesIO()
        await tg_bot.download_file(file.file_path, buffer)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(buffer.getvalue().decode('utf-8'))

    source = await goods_manager.add_source(FileGoodsSource, path)

    await GoodsInfoMenuContext(
        menu_id=MenuIds.goods_source_info,
        source_id=source.source_id,
        trigger=msg,
        callback_override=data.callback_data.copy_history(
            OpenMenu(
                menu_id=MenuIds.goods_source_info,
                context_data={'source_id': source.source_id},
            ),
        ),
    ).build_and_answer(tg_ui, msg)
    utils.delete_message(data.message)


@r.callback_query(cbs.RemoveGoodsSource.filter())
async def remove_goods_source(
    query: CallbackQuery,
    callback_data: cbs.RemoveGoodsSource,
    translater: Tr,
    goods_manager: GoodsSourcesManager,
    tg: Telegram,
):
    if goods_manager.get(callback_data.source_id) is None:
        await query.answer(
            translater.translate('❌ Источник товаров не найден.'),
            show_alert=True,
        )
        return

    await goods_manager.remove_source(callback_data.source_id)

    # Открыть список источников > Открыть меню источника > текущий Query
    await tg.fake_query(join_callbacks(*callback_data.history[:-1]), query)
