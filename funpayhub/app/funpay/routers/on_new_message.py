from __future__ import annotations

from typing import TYPE_CHECKING, Any

from funpaybotengine import Router
from funpaybotengine.dispatching.events import RunnerEvent, NewMessageEvent, ChatChangedEvent

from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.app.telegram.main import Telegram
from funpayhub.app.funpay.filters import is_fph_command
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import NewMessageMenuContext


if TYPE_CHECKING:
    from funpaybotengine import Bot

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
            data=data,
            raise_on_error=not command.ignore_hooks_errors.value,
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
    tg: Telegram,
    tg_ui: UIRegistry,
    data: dict[str, Any],
):
    msgs = []
    checked = []
    for i in events_stack:
        if (
            isinstance(i, NewMessageEvent)
            and i.message.chat_id == event.chat_preview.id
            and i.message.id not in checked
        ):
            checked.append(i.message.id)
            msgs.append(i.message)

    if not msgs:
        return

    context = NewMessageMenuContext(
        chat_id=-1,
        menu_id=MenuIds.new_funpay_message,
        funpay_chat_id=event.chat_preview.id,
        funpay_chat_name=event.chat_preview.username,
        messages=msgs,
    )
    menu = await tg_ui.build_menu(context, data)

    await tg.send_notification(
        'new_message',
        text=menu.text,
        reply_markup=menu.total_keyboard(convert=True),
    )
