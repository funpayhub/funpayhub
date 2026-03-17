from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

from funpayhub.lib.base_app.telegram import utils
from funpayhub.lib.telegram.callback_data import UnknownCallback

from . import callbacks as cbs
from .states import ChangingMenuPage


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery
    from aiogram.fsm.context import FSMContext

    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import UIRegistry
    from funpayhub.lib.base_app.telegram import TelegramApp


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

    ctx_instance = ctx_class(
        menu_id=callback_data.menu_id,
        menu_page=callback_data.menu_page,
        view_page=callback_data.view_page,
        ui_history=callback_data.ui_history,
        trigger=query,
        data=additional_data,
        **callback_data.context_data,
    )
    if callback_data.new_message:
        await query.answer()
        await ctx_instance.build_and_answer(tg_ui, query.message)
    else:
        await ctx_instance.build_and_apply(tg_ui, query.message)


# ----------------------------------------------------
# -------------------- Pagination --------------------
# ----------------------------------------------------
@router.callback_query(cbs.ChangePageTo.filter())
async def page(query: CallbackQuery, callback_data: cbs.ChangePageTo, tg_ui: UIRegistry) -> None:
    print(callback_data.ui_history)
    ctx = tg_ui.context_from_history(callback_data.ui_history)
    ctx.menu_page = callback_data.keyboard if callback_data.keyboard is not None else ctx.menu_page
    ctx.view_page = callback_data.text if callback_data.text is not None else ctx.view_page
    await ctx.build_and_apply(tg_ui, query.message)


@router.callback_query(cbs.ActivateChangingPageState.filter())
async def activate_manual_page_changing_state(
    query: CallbackQuery,
    state: FSMContext,
    callback_data: cbs.ActivateChangingPageState,
    translater: Tr,
):
    await query.answer()
    await ChangingMenuPage(
        query=query,
        mode=callback_data.mode,
        max_pages=callback_data.total_pages,
        state_msg=await query.message.answer(
            text=translater.translate('🔢 Введите номер страницы.'),
        ),
    ).set(state)


@router.message(ChangingMenuPage.filter())
async def change_page_from_message(message: Message, state: FSMContext, tg_ui: UIRegistry) -> None:
    if not message.text.isnumeric():
        return

    new_page_index = int(message.text) - 1

    data = await ChangingMenuPage.get(state)
    if data.max_pages != -1 and (new_page_index > data.max_pages - 1 or new_page_index < 0):
        return

    await state.clear()
    utils.delete_message(data.state_msg)

    ctx = tg_ui.context_from_history(data.ui_history)
    if data.mode == 'keyboard':
        ctx.menu_page = new_page_index
    else:
        ctx.view_page = new_page_index

    await ctx.build_and_answer(tg_ui, message)


@router.callback_query(cbs.GoBack.filter())
async def go_back(query: CallbackQuery, callback_data: cbs.GoBack, tg_ui: UIRegistry) -> None:
    if not callback_data.ui_history:
        await query.answer()
        return
    await tg_ui.context_from_history(callback_data.ui_history).build_and_apply(
        tg_ui,
        query.message,
    )


# ----------------------------------------------------
# ----------------------- Other ----------------------
# ----------------------------------------------------
@router.callback_query(cbs.Dummy.filter())
async def dummy(query: CallbackQuery) -> None:
    await query.answer()


@router.callback_query(cbs.ClearState.filter())
async def clear_state(
    query: CallbackQuery,
    callback_data: cbs.ClearState,
    state: FSMContext,
    tg: TelegramApp,
) -> None:
    if callback_data.delete_message:
        await query.message.delete()
    elif callback_data.open_previous and callback_data.history:
        await tg.fake_query(callback_data, query, pack_history=True)
    await state.clear()
