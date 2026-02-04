from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from funpaybotengine import Router
from aiogram.exceptions import TelegramUnauthorizedError
from funpaybotengine.types import Message
from funpaybotengine.runner import EventsStack
from funpaybotengine.dispatching import NewMessageEvent, ChatChangedEvent

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import NewMessageMenuContext


if TYPE_CHECKING:
    from aiogram import Bot as TGBot
    from chat_sync.src.types import Registry, BotRotater
    from chat_sync.src.properties import ChatSyncProperties

    from funpayhub.lib.telegram.ui import Menu, UIRegistry


router = Router(name='chat_sync')
last_event_stacks: dict[int, str] = {}


async def is_setup(
    message: Message,
    plugin_properties: ChatSyncProperties,
    chat_sync_rotater: BotRotater,
    events_stack: EventsStack,
) -> bool:
    if not plugin_properties.sync_chat_id:
        return False
    if len(chat_sync_rotater) < 4:
        return False
    if last_event_stacks.get(message.chat_id) == events_stack.id:
        return False

    return True


@router.on_new_message(is_setup)
async def sync_new_message(
    message: Message,
    chat_sync_registry: Registry,
    tg_ui: UIRegistry,
    tg_bot: TGBot,
    plugin_properties: ChatSyncProperties,
    events_stack: EventsStack,
    chat_sync_rotater: BotRotater,
) -> None:
    global last_event_stacks
    last_event_stacks[message.chat_id] = events_stack.id

    for event in events_stack.events:
        if isinstance(event, ChatChangedEvent) and event.chat_preview.id == message.chat_id:
            chat_event = event
            break
    else:
        return

    telegram_thread_id = chat_sync_registry.get_telegram_thread(message.chat_id)

    if telegram_thread_id is None:
        topic = await tg_bot.create_forum_topic(
            chat_id=plugin_properties.sync_chat_id.value,
            name=f'{chat_event.chat_preview.username} ({message.chat_id})',
            icon_custom_emoji_id='5417915203100613993',
        )
        telegram_thread_id = topic.message_thread_id
        chat_sync_registry.add_chat_pair(message.chat_id, telegram_thread_id)

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
        chat_id=plugin_properties.sync_chat_id.value,
        thread_id=telegram_thread_id,
    )

    asyncio.create_task(
        send_message_task(
            chat_id=plugin_properties.sync_chat_id.value,
            thread_id=telegram_thread_id,
            rotater=chat_sync_rotater,
            menu=await tg_ui.build_menu(context=ctx),
        ),
        name=f'chat_sync-fp{chat_event.chat_preview.id}:tg{plugin_properties.sync_chat_id.value}.{telegram_thread_id}',
    )


async def send_message_task(chat_id: int, thread_id: int, rotater: BotRotater, menu: Menu) -> None:
    while True:
        try:
            bot = rotater.next_bot()
        except StopIteration:
            return

        try:
            await bot.send_message(
                chat_id=chat_id,
                message_thread_id=thread_id,
                text=menu.main_text,
            )
            return
        except TelegramUnauthorizedError:
            rotater.remove_bot(bot.token)
