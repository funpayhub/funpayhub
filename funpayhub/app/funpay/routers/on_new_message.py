from __future__ import annotations
from funpaybotengine import Router
from typing import TYPE_CHECKING, Any
from funpaybotengine.dispatching.filters import all_of

if TYPE_CHECKING:
    from funpaybotengine.dispatching.events import NewMessageEvent
    from funpaybotengine import Bot
    from funpayhub.app.properties.auto_response import AutoResponseEntryProperties
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.lib.hub.text_formatters import FormattersRegistry


on_new_message_router = r = Router(router_id='fph:on_new_message_router')


def commands_filter(event: NewMessageEvent, properties: FunPayHubProperties, data: Any):
    if not event.message.text:
        return False

    lowered_text = event.message.text.lower()
    msg_text = event.message.text

    for command, params in properties.auto_response.entries.items():
        if params.case_sensitive.value:
            if not msg_text.startswith(command + ' ') and not msg_text == command:
                continue
        else:
            if not lowered_text.startswith(command.lower() + ' ') and not lowered_text == command.lower():
                continue

        if not params.react_on_me.value and event.message.from_me:
            return False
        if not params.react_on_others.value and not event.message.from_me:
            return False

        data['_command'] = params
        return True
    return False


def command_has_reply_filter(_command: AutoResponseEntryProperties):
    return _command.reply.value and _command.response_text.value


@r.on_new_message(
    handler_id='fph:process_command',
    filter=all_of(commands_filter, command_has_reply_filter)
)
async def process_command(
    event: NewMessageEvent,
    fp_formatters: FormattersRegistry,
    fp_bot: Bot,
    _command: AutoResponseEntryProperties,
    data: dict[str, Any]
):
    """
    Хэндлер ищет команду в списке команд и выполняет ее.
    """
    command = _command

    if command.reply.value:
        text = await fp_formatters.format_text(
            text=command.response_text.value,
            raise_on_error=command.abort_on_formatters_error.value,
            data=data,
        )

        await text.send(bot=fp_bot, chat_id=event.message.chat_id)

    # todo: Реализовать и использовать funpay.send_message обертку над funpay.bot.send_message
    # которая будет пытаться отправить сообщение несколько раз + разбивать большие сообщения не
    # более мелкие

    # todo: Выполнение хуков
