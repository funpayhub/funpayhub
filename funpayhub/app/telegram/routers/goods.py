import html

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from funpayhub.app.telegram import callbacks as cbs
from funpayhub.app.telegram.ui.builders.context import StateUIContext
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.goods_sources import GoodsSourcesManager
from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.lib.translater import Translater
from funpayhub.app.telegram import states
from aiogram.types import BufferedInputFile
from aiogram import Bot as TGBot
from io import BytesIO
import re


r = router = Router(name='fph:goods')


@router.callback_query(cbs.DownloadGoods.filter())
async def download_goods(
    query: CallbackQuery,
    goods_manager: GoodsSourcesManager,
    translater: Translater,
    callback_data: cbs.DownloadGoods,
):
    source = goods_manager.get(callback_data.source_id)
    if source is None:
        await query.answer(translater.translate('$goods_source_not_found'), show_alert=True)
        return

    goods = await source.get_goods(-1)

    await query.message.answer_document(
        BufferedInputFile('\n'.join(goods).encode('utf-8'), 'goods.txt'),
        caption=f'<b>{html.escape(source.display_id)}</b>'
    )
    await query.answer()


@router.callback_query(cbs.UploadGoods.filter())
async def upload_goods_set_state(
    query: CallbackQuery,
    translater: Translater,
    state: FSMContext,
    tg_ui: UIRegistry,
    callback_data: cbs.UploadGoods,
):
    ctx = StateUIContext(
        menu_id=MenuIds.state_menu,
        delete_on_clear=True,
        text=translater.translate('$upload_goods_text'),
        trigger=query
    )
    menu = await tg_ui.build_menu(ctx)
    msg = await menu.answer_to(query.message)
    
    s = states.UploadingGoods(source_id=callback_data.source_id, message=msg)
    await state.set_state(s.identifier)
    await state.set_data({'data': s})
    await query.answer()


@router.message(StateFilter(states.UploadingGoods.__identifier__))
async def upload_goods(
    message: Message,
    state: FSMContext,
    tg_bot: TGBot,
    goods_manager: GoodsSourcesManager,
    translater: Translater,
):
    data: states.UploadingGoods = (await state.get_data())['data']
    await state.clear()
    await data.message.delete()
    source = goods_manager.get(data.source_id)
    if not source:
        await message.reply(translater.translate('$goods_source_not_found'))
        return
    
    if message.document:
        try:
            io = BytesIO()
            file = await tg_bot.get_file(message.document.file_id)
            await tg_bot.download_file(file.file_path, io)
            new_goods = io.getbuffer().tobytes().decode('utf-8').splitlines()
        except:
            await message.reply(translater.translate('$error_uploading_goods'))
            return

    else:
        new_goods = message.text.split('\n')

    await source.set_goods(new_goods)
    await message.answer(translater.translate('$goods_uploaded'))


@router.callback_query(cbs.RemoveGoods.filter())
async def upload_goods_set_state(
    query: CallbackQuery,
    translater: Translater,
    state: FSMContext,
    tg_ui: UIRegistry,
    callback_data: cbs.UploadGoods,
):
    ctx = StateUIContext(
        menu_id=MenuIds.state_menu,
        delete_on_clear=True,
        text=translater.translate('$remove_goods_text'),
        trigger=query
    )
    menu = await tg_ui.build_menu(ctx)
    msg = await menu.answer_to(query.message)

    s = states.RemovingGoods(source_id=callback_data.source_id, message=msg)
    await state.set_state(s.identifier)
    await state.set_data({'data': s})
    await query.answer()


amount_re = re.compile(r'(\d+)-(\d+)')


@router.message(StateFilter(states.RemovingGoods.identifier))
async def upload_goods(
    message: Message,
    state: FSMContext,
    goods_manager: GoodsSourcesManager,
    translater: Translater,
):
    data: states.RemovingGoods = (await state.get_data())['data']
    await state.clear()
    await data.message.delete()
    source = goods_manager.get(data.source_id)
    if not source:
        await message.reply(translater.translate('$goods_source_not_found'))
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
        await message.reply(translater.translate('$error_removing_goods_wrong_format'))
        return


    await source.remove_goods(start_index, amount)
    await message.answer(translater.translate('$goods_removed'))