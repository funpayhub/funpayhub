from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiogram import Bot, Router
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from funpayhub.lib.telegram.ui import UIRegistry, MenuContext

from . import callbacks as cbs
from . import states
import os

from ..properties import FunPayHubProperties


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.telegram.main import Telegram


setup_chat: int | None = None


router = Router()
setup_started = asyncio.Event()


@router.message(lambda m, hub: m.text == hub.instance_id and not setup_started.is_set())
async def start_setup(msg: Message, tg_bot: Bot, tg_ui: UIRegistry):
    if setup_started.is_set():
        return

    setup_started.set()
    async with ChatActionSender.typing(msg.chat.id, tg_bot, msg.message_thread_id):
        menu = await tg_ui.build_menu(
            MenuContext(menu_id='fph:setup_select_language', trigger=msg),
        )
        await menu.reply_to(msg)


@router.callback_query(cbs.SelectSetupLanguage.filter())
async def open_select_proxy_menu(
    cb: CallbackQuery,
    tg_ui: UIRegistry,
    tg: Telegram,
    callback_data: cbs.SelectSetupLanguage,
    properties: FunPayHubProperties,
    hub: FunPayHub,
):
    await properties.general.language.set_value(callback_data.lang)
    await hub.emit_parameter_changed_event(properties.general.language)

    menu = await tg_ui.build_menu(
        MenuContext(
            menu_id='fph:setup_enter_proxy',
            trigger=cb,
            data={
                'proxy_env': bool(os.environ.get('FPH_PROXY')),
                'proxy_props': bool(True)  # todo proxy property
            }
        )
    )
    await menu.apply_to(cb.message)
    state = states.EnteringProxyState(message=cb.message, callback_data=callback_data)
    ctx = tg.dispatcher.fsm.get_context(
        tg.bot,
        cb.message.chat.id,
        cb.from_user.id,
        cb.message.message_thread_id
    )
    await ctx.set_state(state.identifier)
    await ctx.set_data({'data': state})


@router.message(StateFilter(states.EnteringProxyState.identifier))
async def check_proxy_and_open_select_user_agent_menu():
    ...


@router.callback_query(cbs.SetupProxy.filter())
async def setup_proxy_and_open_select_user_agent_menu():
    ...