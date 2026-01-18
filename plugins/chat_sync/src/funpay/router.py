from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiogram import Bot as TGBot
from funpaybotengine import Router
from funpaybotengine.types import Message
from funpaybotengine.runner import EventsStack
from funpaybotengine.dispatching import NewMessageEvent

from funpayhub.app.properties import FunPayHubProperties
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import NewMessageMenuContext

from .filter import is_setup


if TYPE_CHECKING:
    from chat_sync.src.types import Registry, BotRotater
    from chat_sync.src.properties import ChatSyncProperties

    from funpayhub.lib.telegram.ui import Menu, UIRegistry


router = Router(name='chat_sync')


@router.on_new_message(is_setup)
async def sync_new_message(
    message: Message,
    chat_sync_registry: Registry,
    tg_ui: UIRegistry,
    properties: FunPayHubProperties,
    events_stack: EventsStack,
    chat_sync_rotater: BotRotater,
):
    pl_props: ChatSyncProperties = properties.plugin_properties.get_properties['chat_sync']
    telegram_thread_id = chat_sync_registry.get_telegram_thread(message.chat_id)
    if telegram_thread_id is None:
        bot = chat_sync_rotater.next_bot()
        topic = await bot.create_forum_topic(
            chat_id=pl_props.sync_chat_id.value,
            name=f'{message.chat_name} ({message.chat_id})',
        )
        telegram_thread_id = topic.message_thread_id
        await chat_sync_registry.add_chat_pair(message.chat_id, telegram_thread_id)

    messages = [
        i.message
        for i in events_stack.events
        if isinstance(i, NewMessageEvent) and i.message.chat_id == message.chat_id
    ]

    ctx = NewMessageMenuContext(
        menu_id=MenuIds.new_funpay_message,
        funpay_chat_id=message.chat_id,
        funpay_chat_name=message.chat_name,
        messages=messages,
        chat_id=pl_props.sync_chat_id.value,
        thread_id=telegram_thread_id,
    )

    asyncio.create_task(
        send_message_task(
            chat_id=pl_props.sync_chat_id.value,
            thread_id=telegram_thread_id,
            bot=chat_sync_rotater.next_bot(),
            menu=await tg_ui.build_menu(context=ctx),
        ),
    )


async def send_message_task(chat_id: int, thread_id: int, bot: TGBot, menu: Menu):
    await bot.send_message(
        chat_id=chat_id,
        message_thread_id=thread_id,
        text=menu.text,
    )
