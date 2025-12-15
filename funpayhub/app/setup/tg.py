from __future__ import annotations

import asyncio

from aiogram import Bot, Router
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from funpayhub.lib.telegram.ui import UIRegistry, MenuContext

from . import callbacks as cbs


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
async def open_select_proxy_menu(cb: CallbackQuery, tg_ui: UIRegistry):
    menu = await tg_ui.build_menu(MenuContext(menu_id='fph:setup_enter_proxy', trigger=cb))
    await menu.apply_to(cb.message)
