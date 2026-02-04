from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from aiogram.filters import StateFilter
import funpayhub.app.telegram.callbacks as cbs
from .states import ChangingMenuPage
from funpayhub.lib.telegram.callback_data import UnknownCallback
from aiogram import Router
from funpayhub.lib.base_app.telegram import utils


if TYPE_CHECKING:
    from funpayhub.lib.base_app.telegram import TelegramApp
    from aiogram.types import Message, CallbackQuery
    from aiogram.fsm.context import FSMContext


router = Router(name='app:base_ui')


# ----------------------------------------------------
# -------------------- Pagination --------------------
# ----------------------------------------------------
@router.callback_query(cbs.ChangePageTo.filter())
async def change_page(
    query: CallbackQuery,
    callback_data: cbs.ChangePageTo,
    tg: TelegramApp
) -> None:
    old = UnknownCallback.parse(callback_data.history[-1])
    if callback_data.menu_page is not None:
        old.data['menu_page'] = callback_data.menu_page
    if callback_data.view_page is not None:
        old.data['view_page'] = callback_data.view_page
    old.history = callback_data.history[:-1]

    await tg.fake_query(old.pack(), query)


@router.callback_query(cbs.ChangeMenuPageManually.filter())
@router.callback_query(cbs.ChangeViewPageManually.filter())
async def activate_manual_page_changing_state(
    query: CallbackQuery,
    state: FSMContext,
    callback_data: cbs.ChangeMenuPageManually | cbs.ChangeViewPageManually
):
    msg = await query.message.answer(text='$enter_new_page_index_message')

    data = ChangingMenuPage(
        mode='keyboard' if isinstance(callback_data, cbs.ChangeMenuPageManually) else 'text',
        query=query,
        message=msg,
        max_pages=callback_data.total_pages,
    )

    await state.set_state(data.identifier)
    await state.set_data({'data': data})
    await query.answer()


@router.message(StateFilter(ChangingMenuPage.identifier))
async def change_page_from_message(message: Message, state: FSMContext, tg: TelegramApp) -> None:
    asyncio.create_task(utils.delete_message(message))

    if not message.text.isnumeric():
        return
    new_page_index = int(message.text) - 1

    data: ChangingMenuPage = (await state.get_data())['data']
    if data.max_pages != -1 and (new_page_index > data.max_pages - 1 or new_page_index < 0):
        return

    await state.clear()
    asyncio.create_task(utils.delete_message(data.message))

    old = UnknownCallback.from_string(data.callback_data.history[-1])
    old.data['view_page' if data.mode == 'text' else 'menu_page'] = new_page_index
    old.history = data.callback_data.history[:-1]
    await tg.fake_query(callback_data=old.pack(), query=data.query)
