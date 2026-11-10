from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F
from aiogram.types import (
    Message,
    CallbackQuery as Query,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager, MenuContext
from hubplatform.telegram.ui.session import MenuFrame
from hubplatform.app.components.telegram.utils import abort_input, finish_input

from . import (
    states,
    callbacks as cbs,
)
from .ui import TIME_FORMAT_HINT, ChatInputMenuContext, parse_ts
from ..menu_ids import MenuIDs as ExtensionMenuIDs


if TYPE_CHECKING:
    from dothub.app.components.funpay_component.first_response_cache import FirstResponseCache


router = Router(name='app:funpay_component:telegram_extension:first_response_cache')


@router.message(Command('first_response_cache'))
async def open_first_response_cache_menu(m: Message, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=ExtensionMenuIDs.first_response_cache.chats_list,
        context=MenuContext(),
        environment=m,
    )


@router.callback_query(cbs.SetChatTimestampToNow.filter())
async def set_chat_timestamp_to_now(
    q: Query,
    cbd: cbs.SetChatTimestampToNow,
    first_response_cache: FirstResponseCache,
    telegram_ui_manager: UIManager,
) -> None:
    await first_response_cache.update(cbd.chat_id)
    async with telegram_ui_manager.edit_session(
        session_id=cbd.session_id,
        rerender=True,
        trigger=q,
    ):
        pass
    await q.answer('🕒 Время обновлено.')


@router.callback_query(cbs.RemoveChatFromCache.filter())
async def remove_chat_from_cache(
    q: Query,
    cbd: cbs.RemoveChatFromCache,
    first_response_cache: FirstResponseCache,
    telegram_ui_manager: UIManager,
) -> None:
    await first_response_cache.remove(cbd.chat_id)
    async with telegram_ui_manager.edit_session(
        session_id=cbd.session_id,
        rerender=True,
        trigger=q,
    ) as s:
        if s.history:
            s.current = s.history.pop()
        else:
            s.current = MenuFrame.from_menu_context(
                menu_id=ExtensionMenuIDs.first_response_cache.chats_list,
                menu_context=MenuContext(),
            )
    await q.answer('🗑 Чат удалён из кэша.')


@router.callback_query(cbs.StartChatInput.filter())
async def start_chat_input(
    q: Query,
    cbd: cbs.StartChatInput,
    state: FSMContext,
    telegram_ui_manager: UIManager,
) -> None:
    result = await telegram_ui_manager.open_menu(
        menu_id=ExtensionMenuIDs.first_response_cache.chat_input,
        context=ChatInputMenuContext(
            action=cbd.action,
            chat_id=cbd.chat_id,
            return_session_id=cbd.session_id,
        ),
        environment=q,
    )
    await states.EnteringChatData(
        action=cbd.action,
        chat_id=cbd.chat_id,
        return_session_id=cbd.session_id,
        input_session_id=result.session.id,
    ).set(state)
    await q.answer()


@router.message(states.EnteringChatData.filter(F.action == 'add'))
async def add_chat(
    m: Message,
    state: FSMContext,
    first_response_cache: FirstResponseCache,
    telegram_ui_manager: UIManager,
) -> None:
    data = await states.EnteringChatData.get(state)
    if not m.text or not m.text.strip().isdigit():
        await m.answer('❌ ID чата должен быть числом.')
        return

    await first_response_cache.update(int(m.text.strip()))
    await finish_input(
        m,
        state,
        telegram_ui_manager,
        data.return_session_id,
        data.input_session_id,
    )


@router.message(states.EnteringChatData.filter(F.action == 'set_time'))
async def set_chat_time(
    m: Message,
    state: FSMContext,
    first_response_cache: FirstResponseCache,
    telegram_ui_manager: UIManager,
) -> None:
    data = await states.EnteringChatData.get(state)
    if data.chat_id is None:
        await abort_input(m, state, telegram_ui_manager, data.input_session_id)
        return

    try:
        ts = parse_ts(m.text or '')
    except ValueError:
        await m.answer(f'❌ Неверный формат. Ожидается {TIME_FORMAT_HINT}.')
        return

    await first_response_cache.update(data.chat_id, ts=ts)
    await finish_input(
        m,
        state,
        telegram_ui_manager,
        data.return_session_id,
        data.input_session_id,
    )
