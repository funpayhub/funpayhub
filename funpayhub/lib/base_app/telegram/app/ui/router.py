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
# ------------------ Menu Rendering ------------------
# ----------------------------------------------------
@router.callback_query(cbs.OpenMenu.filter())
async def open_custom_menu(
    query: CallbackQuery,
    tg_ui: UIRegistry,
    callback_data: cbs.OpenMenu,
) -> None:
    menu_builder = tg_ui.get_menu_builder(callback_data.menu_id)
    ctx_class = menu_builder.builder.context_type
    additional_data = {**callback_data.data}

    parsed_callback: UnknownCallback = getattr(query, '__parsed__', None)
    if parsed_callback is not None:
        parsed_callback.data['new_message'] = False

    if callback_data.replace_history_with_trigger:
        fake_callback_history = cbs.DrawMenu(
            text=query.message.text,
            keyboard=cbs.DrawMenu.keyboard_from_message(query.message),
        ).pack(hash=False)

        fake_callback_data = callback_data.model_copy()
        fake_callback_data.history = [fake_callback_history]
        additional_data['callback_data'] = fake_callback_data

    ctx_instance = ctx_class(
        menu_id=callback_data.menu_id,
        menu_page=callback_data.menu_page,
        view_page=callback_data.view_page,
        trigger=query,
        data=additional_data,
        **callback_data.context_data,
    )
    if callback_data.new_message:
        await ctx_instance.build_and_answer(tg_ui, query.message)
    else:
        await ctx_instance.build_and_apply(tg_ui, query.message)


@router.callback_query(cbs.DrawMenu.filter())
async def draw_menu(
    query: CallbackQuery,
    callback_data: cbs.DrawMenu,
):
    kb_list = []
    for row in callback_data.keyboard:
        curr_row = []
        for button in row:
            curr_row.append(
                InlineKeyboardButton(
                    text=button.get('text'),
                    callback_data=button.get('callback_data'),
                    url=button.get('url'),
                ),
            )
        kb_list.append(curr_row)

    kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
    await query.message.edit_text(
        text=callback_data.text,
        reply_markup=kb,
    )


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



# ----------------------------------------------------
# ----------------------- Other ----------------------
# ----------------------------------------------------
@router.callback_query(cbs.Dummy.filter())
async def dummy(query: CallbackQuery) -> None:
    await query.answer()


@router.callback_query(cbs.Clear.filter())
async def clear(
    query: CallbackQuery,
    callback_data: cbs.Clear,
    state: FSMContext,
    tg: Telegram
) -> None:
    if callback_data.delete_message:
        await query.message.delete()
    elif callback_data.open_previous and callback_data.history:
        await tg.execute_previous_callback(callback_data, query)
    await state.clear()