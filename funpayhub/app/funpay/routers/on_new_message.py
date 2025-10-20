from __future__ import annotations

from typing import TYPE_CHECKING, Any

from funpaybotengine import Router

from funpayhub.app.funpay.filters import is_fph_command
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.app.telegram.ui.builders.context import NewMessageMenuContext
from funpaybotengine.dispatching.events import ChatChangedEvent, NewMessageEvent, RunnerEvent
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui import UIRegistry
import asyncio

if TYPE_CHECKING:
    from funpaybotengine import Bot
    from aiogram import Bot as TGBot

    from funpayhub.lib.hub.text_formatters import FormattersRegistry
    from funpayhub.app.properties.auto_response import AutoResponseEntryProperties


on_new_message_router = r = Router(name='fph:on_new_message_router')


@r.on_new_message(is_fph_command, handler_id='fph:process_command')
async def process_command(
    event: NewMessageEvent,
    fp_formatters: FormattersRegistry,
    fp_bot: Bot,
    command: AutoResponseEntryProperties,
    data: dict[str, Any],
):
    """
    Хэндлер ищет команду в списке команд и выполняет ее.
    """
    command = command

    if command.reply.value:
        text = await fp_formatters.format_text(
            text=command.response_text.value,
            raise_on_error=not command.ignore_hooks_errors.value,
            data=data,
        )

        await text.send(bot=fp_bot, chat_id=event.message.chat_id)

    # todo: Реализовать и использовать funpay.send_message обертку над funpay.bot.send_message
    # которая будет пытаться отправить сообщение несколько раз + разбивать большие сообщения не
    # более мелкие

    # todo: Выполнение хуков


@r.on_chat_changed(handler_id='fph:new_message_notification')
async def send_new_message_notification(
    event: ChatChangedEvent,
    events_stack: list[RunnerEvent],
    properties: FunPayHubProperties,
    tg_bot: TGBot,
    tg_ui: UIRegistry,
    data: dict[str, Any]
):
    msgs = [i.message for i in events_stack if isinstance(i, NewMessageEvent) and i.message.chat_id == event.chat_preview.id]
    if not msgs:
        return
    chats = properties.telegram.notifications.new_message.value
    if not chats:
        return
    context = NewMessageMenuContext(
        chat_id=-1,
        menu_id=MenuIds.new_message,
        funpay_chat_id=event.chat_preview.id,
        funpay_chat_name=event.chat_preview.username,
        messages=msgs
    )
    menu = await tg_ui.build_menu(context, data)

    for i in chats:
        split = i.split('.')
        chat_id, thread_id = int(split[0]), int(split[1]) if split[1].isnumeric() else None

        asyncio.create_task(tg_bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=menu.text,
            reply_markup=menu.total_keyboard(convert=True)
        ))
