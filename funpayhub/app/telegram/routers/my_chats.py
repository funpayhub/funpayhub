from __future__ import annotations

import time
from dataclasses import field, dataclass
from asyncio import Lock

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from funpaybotengine import Bot
from funpaybotengine.types import PrivateChatPreview

from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import MyChatsMenuContext


router = Router(name='fph:my_chats')


@dataclass
class MyChats:
    lock: Lock = Lock()
    chats: dict[int, PrivateChatPreview] = field(default_factory=dict)
    timestamp: float = 0

    async def update(self, bot: Bot):
        async with self.lock:
            self.chats = {i.id: i for i in await bot.get_recent_chat_previews()}
            self.timestamp = time.time()


MY_CHATS = MyChats()


@router.message(Command('chats'))
async def send_my_chats_ui(msg: Message, fp_bot: Bot, tg_ui: UIRegistry):
    if not MY_CHATS.timestamp:
        await MY_CHATS.update(fp_bot)

    context = MyChatsMenuContext(
        trigger=msg,
        chats=MY_CHATS,
        menu_id=MenuIds.my_chats,
    )

    menu = await tg_ui.build_menu(context)

    await menu.reply_to(msg)
