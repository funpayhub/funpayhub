from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Router

from funpayhub.lib.base_app.telegram import utils

from . import callbacks as cbs
from .states import ChangingMenuPage


if TYPE_CHECKING:
    from aiogram.types import (
        Message,
        CallbackQuery as Query,
    )
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import UIRegistry as UI
    from funpayhub.lib.telegram.callback_data import UnknownCallback


router = Router(name='app:base_ui')


# ----------------------------------------------------
# ------------------ Menu Rendering ------------------
# ----------------------------------------------------
@router.callback_query(cbs.OpenMenu.filter())
async def open_custom_menu(q: Query, tg_ui: UI, cbd: cbs.OpenMenu) -> Any:
    menu_builder = tg_ui.get_menu_builder(cbd.menu_id)
    ctx_class = menu_builder.builder.context_type
    additional_data = {**cbd.data}

    parsed_callback: UnknownCallback = getattr(q, '__parsed__', None)
    if parsed_callback is not None:
        parsed_callback.data['new_message'] = False

    ctx_instance = ctx_class(
        menu_id=cbd.menu_id,
        trigger=q,
        menu_page=cbd.menu_page,
        view_page=cbd.view_page,
        ui_history=cbd.ui_history,
        data=additional_data,
        **cbd.context_data,
    )
    await ctx_instance.answer_to() if cbd.new_message else await ctx_instance.apply_to()


# ----------------------------------------------------
# -------------------- Pagination --------------------
# ----------------------------------------------------
@router.callback_query(cbs.ChangePageTo.filter())
async def page(q: Query, cbd: cbs.ChangePageTo, tg_ui: UI) -> None:
    ctx = tg_ui.context_from_history(cbd.ui_history, trigger=q)
    ctx.menu_page = cbd.keyboard if cbd.keyboard is not None else ctx.menu_page
    ctx.view_page = cbd.text if cbd.text is not None else ctx.view_page
    await ctx.apply_to()


@router.callback_query(cbs.ActivateChangingPageState.filter())
async def activate_manual_page_changing_state(
    q: Query,
    state: FSM,
    callback_data: cbs.ActivateChangingPageState,
    translater: Tr,
):
    await q.answer()
    await ChangingMenuPage(
        query=q,
        mode=callback_data.mode,
        max_pages=callback_data.total_pages,
        state_msg=await q.message.answer(translater.translate('🔢 Введите номер страницы.')),
    ).set(state)


@router.message(ChangingMenuPage.filter())
async def change_page_from_message(m: Message, state: FSM, tg_ui: UI) -> None:
    if not m.text.isnumeric():
        return

    new_page_index = int(m.text) - 1

    data = await ChangingMenuPage.get(state)
    if data.max_pages != -1 and (new_page_index > data.max_pages - 1 or new_page_index < 0):
        return

    await state.clear()
    utils.delete_message(data.state_msg)

    ctx = tg_ui.context_from_history(data.ui_history, trigger=m)
    if data.mode == 'keyboard':
        ctx.menu_page = new_page_index
    else:
        ctx.view_page = new_page_index

    await ctx.answer_to()


@router.callback_query(cbs.GoBack.filter())
async def go_back(q: Query, cbd: cbs.GoBack, tg_ui: UI) -> Any:
    if not cbd.ui_history:
        return q.answer()

    await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to(ui_registry=tg_ui)


# ----------------------------------------------------
# ----------------------- Other ----------------------
# ----------------------------------------------------
@router.callback_query(cbs.Dummy.filter())
async def dummy(q: Query) -> None:
    await q.answer()


@router.callback_query(cbs.ClearState.filter())
async def clear_state(q: Query, cbd: cbs.ClearState, state: FSM, tg_ui: UI) -> None:
    await state.clear()
    if cbd.delete_message:
        await q.message.delete()
    elif cbd.open_previous and cbd.ui_history:
        await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to()
