from __future__ import annotations

from typing import TYPE_CHECKING, Any

from funpaybotengine import Router
from funpayhub.app.funpay.filters import is_fph_command


if TYPE_CHECKING:
    from funpaybotengine import Bot
    from funpaybotengine.dispatching.events import NewMessageEvent

    from funpayhub.lib.hub.text_formatters import FormattersRegistry
    from funpayhub.app.properties.auto_response import AutoResponseEntryProperties


on_new_message_router = r = Router(name='fph:on_new_message_router')



@r.on_new_message(
    is_fph_command,
    handler_id='fph:process_command',
)
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
