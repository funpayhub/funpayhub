from __future__ import annotations

import re
from typing import TYPE_CHECKING
from aiogram import Router
from aiogram.filters import Command
from io import BytesIO

from funpaybotengine.exceptions import FunPayBotEngineError
import asyncio

if TYPE_CHECKING:
    from chat_sync.src.properties import ChatSyncProperties
    from aiogram.types import Message, ReactionTypeEmoji
    from chat_sync.src.types import Registry, BotRotater
    from funpayhub.app.main import FunPayHub
    from aiogram import Bot as TGBot


r = router = Router(name='chat_sync')
checking_chat_lock = asyncio.Lock()


async def need_to_resend(
    message: Message,
    plugin_properties: ChatSyncProperties,
    chat_sync_registry: Registry
) -> bool:
    return (
        message.chat.id == plugin_properties.sync_chat_id.value and
        message.message_thread_id in chat_sync_registry.tg_to_fp_pairs
    )


@r.message(Command('chat_sync'))
async def setup_chat_sync_chat(
    message: Message,
    plugin_properties: ChatSyncProperties,
):
    if plugin_properties.sync_chat_id.value:
        await message.answer(
            '❌ Sync-чат уже установлен. '
            'Если хотите изменить sync-чат - сначала сбросьте его в параметрах.'
        )
        return

    if not message.chat.is_forum:
        await message.answer('❌ Чат не является форумом.')
        return


    await plugin_properties.sync_chat_id.set_value(message.chat.id)
    await message.answer('✅ Sync-чат установлен.')


@r.message(~Command(re.compile('\S+')), need_to_resend)
async def send_to_funpay_chat(message: Message, chat_sync_registry: Registry, hub: FunPayHub):
    funpay_chat_id = chat_sync_registry.tg_to_fp_pairs[message.message_thread_id]

    image: BytesIO | None = None
    text: str | None = None

    if message.photo:
        file = await message.bot.get_file(message.photo[-1].file_id)
        buffer = BytesIO()
        await message.bot.download_file(file.file_path, buffer)
        image = buffer
    elif message.text:
        text = message.text
    else:
        return

    try:
        await hub.funpay.send_message(
            funpay_chat_id,
            text=text,
            image=image,
            automatic_message=False
        )
        try:
            emoji = ReactionTypeEmoji(emoji='🎉')
            await message.react(reaction=[emoji], is_big=True)
        except:
            pass
    except FunPayBotEngineError:
        emoji = ReactionTypeEmoji(emoji='💩')
        await message.react(reaction=[emoji], is_big=True)

