from __future__ import annotations

import re
import html
from typing import TYPE_CHECKING, Any
from io import BytesIO
from pathlib import Path

from aiogram import Router
from aiogram.types import (
    Message,
    CallbackQuery as Query,
    BufferedInputFile,
)
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest

from funpayhub.lib.translater import translater
from funpayhub.lib.goods_sources import GoodsSource, FileGoodsSource
from funpayhub.lib.base_app.telegram import utils

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
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.lib.telegram.ui import UIRegistry as UI
    from funpayhub.lib.goods_sources import GoodsSourcesManager as GoodsManager


r = router = Router(name='fph:goods')
ru = translater.translate


# -------- Helpers --------
async def _get_source(trigger: Query | Message, source_id: str) -> GoodsSource | None:
    source = get_wfd().goods_manager.get(source_id)
    if source is None:
        text = ru('❌ Источник товаров {source_id} не найден.', source_id=source_id)
        if isinstance(trigger, Query):
            await trigger.answer(text, show_alert=True)
        elif isinstance(trigger, Message):
            await trigger.reply(text)
        return None
    return source


async def _get_goods_from_message(message: Message) -> list[str]:
    if message.document:
        io = BytesIO()
        file = await message.bot.get_file(message.document.file_id)
        await message.bot.download_file(file.file_path, io)
        return io.getbuffer().tobytes().decode('utf-8').splitlines()
    return message.text.split('\n')


# -------- Handlers --------
@router.callback_query(cbs.DownloadGoods.filter())
async def download_goods(q: Query, cbd: cbs.DownloadGoods) -> None:
    if (source := await _get_source(q, cbd.source_id)) is None:
        return

    goods = await source.get_goods(-1)

    await q.message.answer_document(
        BufferedInputFile('\n'.join(goods).encode('utf-8'), 'goods.txt'),
        caption=f'<b>{html.escape(source.display_id)}</b>',
    )
    await q.answer()


@router.callback_query(cbs.ReloadGoodsSource.filter())
async def reload_goods(q: Query, cbd: cbs.ReloadGoodsSource, tg_ui: UI) -> None:
    if (await _get_source(q, cbd.source_id)) is None:
        await q.answer()
        return

    try:
        await q.answer()
        await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to()
    except TelegramBadRequest:
        pass


@router.callback_query(cbs.UploadGoods.filter())
@router.callback_query(cbs.RemoveGoods.filter())
@router.callback_query(cbs.AddGoods.filter())
async def upload_goods_set_state(
    q: Query,
    state: FSM,
    cbd: cbs.UploadGoods | cbs.RemoveGoods | cbs.AddGoods,
) -> Any:
    mapping = {
        cbs.UploadGoods: (
            ru(
                '📤 Отправьте список товаров или файл с товарами (каждый товар с новой строки).\n\n'
                '⚠️ Важно: это <b><u>перезапишет</u></b> текущие товары, а не добавит новые.\n'
                'Если вы хотите добавить новые товары к существующим, '
                'используйте кнопку <i>Добавить товары</i>.',
            ),
            states.UploadingGoods,
        ),
        cbs.RemoveGoods: (
            ru(
                '🗑️ Укажите номер товара или диапазон для удаления. '
                'Например: <code>1</code> или <code>1-7</code>.\n\n'
                '⚠️ Будьте внимательны: выбранные товары будут удалены '
                'без возможности восстановления.',
            ),
            states.RemovingGoods,
        ),
        cbs.AddGoods: (
            ru(
                '➕ Пришлите список товаров или файл с товарами, '
                'где каждая новая строка — отдельный товар.\n\n'
                '⚠️ Важно: новые товары будут <b><u>добавлены</u></b> к текущему списку, '
                'а не перезапишут его.\n'
                'Чтобы заменить весь список, используйте кнопку <i>Выгрузить товары</i>.',
            ),
            states.AddingGoods,
        ),
    }

    text, state_cls = mapping[type(cbd)]
    msg = await StateUIContext(menu_id=MenuIds.state_menu, trigger=q, text=text).answer_to()
    await state_cls(query=q, source_id=cbd.source_id, state_message=msg).set(state)


@router.message(states.UploadingGoods.filter())
@router.message(states.AddingGoods.filter())
async def upload_goods(m: Message, state: FSM, tg_ui: UI) -> Any:
    try:
        data = await states.UploadingGoods.clear(state)
    except RuntimeError:
        data = await states.AddingGoods.clear(state)
    utils.delete_message(data.state_message)

    if (source := await _get_source(m, data.source_id)) is None:
        return None

    try:
        new_goods = await _get_goods_from_message(m)
    except:
        return m.reply(
            ru(
                '<b>❌ Не удалось получить товары из сообщения или файла. '
                'Проверьте корректность данных. Подробности в логах.</b>',
            ),
        )

    if isinstance(data, states.UploadingGoods):
        await source.set_goods(new_goods)
    elif isinstance(data, states.AddingGoods):
        await source.add_goods(new_goods)

    await tg_ui.context_from_history(data.ui_history, trigger=m).answer_to()


amount_re = re.compile(r'(\d+)-(\d+)')


@router.message(states.RemovingGoods.filter())
async def remove_goods(m: Message, state: FSM, tg_ui: UI) -> Any:
    data = await states.RemovingGoods.get(state)
    if (source := await _get_source(m, data.source_id)) is None:
        await states.RemovingGoods.clear(state, raise_=False)
        return m.answer(
            ru('<b>❌ Источник товаров {source_id} не найден.</b>', source_id=data.source_id),
        )

    start_index, amount = None, None
    text = m.text.replace(' ', '')
    if text.isnumeric():
        start_index, amount = int(text) - 1, 1
    elif amount_re.fullmatch(text):
        start_index, end_index = (int(i) - 1 for i in text.split('-'))
        if end_index > start_index:
            amount = end_index - start_index + 1

    if start_index is None or amount is None or start_index < 0:
        return m.reply(
            ru(
                '❌ Неверный формат ввода. '
                'Укажите номер товара или диапазон через дефис, например: <'
                'code>1</code> или <code>1-7</code>.',
            ),
        )

    await states.RemovingGoods.clear(state, raise_=False)
    await source.remove_goods(start_index, amount)
    await tg_ui.context_from_history(data.ui_history, trigger=m).answer_to()


@router.callback_query(cbs.AddGoodsTxtSource.filter())
async def set_adding_source_st(q: Query, state: FSM) -> Any:
    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        text=ru(
            '<b>📄 Отправьте название файла или сам файл. '
            'Если вы пришлете файл, будет использовать его имя.</b>',
        ),
        trigger=q,
    ).answer_to()

    await states.AddingGoodsTxtSource(query=q, state_message=msg).set(state)


INVALID_CHARS = set('<>:"/\\|?*\0')


@router.message(StateFilter(states.AddingGoodsTxtSource.identifier))
async def add_source(m: Message, state: FSM, tg_bot: TGBot, goods_manager: GoodsManager) -> Any:
    data = await states.AddingGoodsTxtSource.get(state)
    filename = m.text if m.text else m.document.file_name if m.document else ''

    if not filename:
        return m.reply(ru('<b>❌ Имя файла не может быть пустым.</b>'))

    if (
        filename in ['.', '..']
        or filename.endswith((' ', '.'))
        or any(c in INVALID_CHARS for c in filename)
        or any(ord(c) < 32 for c in filename)
    ):
        return m.reply(ru('<b>❌ Невалидное имя файла.</b>'))

    path = Path('storage/goods') / filename
    if not path.suffix == '.txt':
        path = path.with_suffix('.txt')
    new_id = 'file://' + str(path)

    if new_id in goods_manager:
        await m.reply(ru('<b>❌ Файл {file} уже существует.</b>', file=str(path)))

    await state.clear()

    if m.document:
        file = await tg_bot.get_file(m.document.file_id)
        buffer = BytesIO()
        await tg_bot.download_file(file.file_path, buffer)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(buffer.getvalue().decode('utf-8'))

    source = await goods_manager.add_source(FileGoodsSource, path)

    await GoodsInfoMenuContext(
        menu_id=MenuIds.goods_source_info,
        trigger=m,
        source_id=source.source_id,
        ui_history=data.ui_history,
    ).answer_to()
    utils.delete_message(data.message)


@r.callback_query(cbs.RemoveGoodsSource.filter())
async def del_source(
    q: Query,
    cbd: cbs.RemoveGoodsSource,
    goods_manager: GoodsManager,
    tg_ui: UI,
) -> Any:
    if goods_manager.get(cbd.source_id) is None:
        return q.answer(ru('❌ Источник товаров не найден.'), show_alert=True)

    await goods_manager.remove_source(cbd.source_id)
    await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to()
