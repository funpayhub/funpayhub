from __future__ import annotations
from funpaybotengine import Router
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from funpaybotengine.dispatching.events import NewMessageEvent
    from funpaybotengine import Bot
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.lib.hub.text_formatters import FormattersRegistry


on_new_message_router = r = Router(router_id='fph:on_new_message_router')


@r.on_new_message(handler_id='fph:process_command')
async def process_command(
    event: NewMessageEvent,
    properties: FunPayHubProperties,
    fp_formatters: FormattersRegistry,
    fp_bot: Bot,
    data: dict[str, Any]
):
    if not event.message.text or event.message.text not in properties.auto_response.entries:
        return
    command = properties.auto_response.entries[event.message.text]

    if event.message.from_me and not command.react_on_me.value:
        return
    if not event.message.from_me and not command.reaco_on_me.value:
        return

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