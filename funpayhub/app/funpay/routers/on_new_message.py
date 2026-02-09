from __future__ import annotations

from typing import TYPE_CHECKING, Any

from funpaybotengine import Router
from funpaybotengine.dispatching.events import RunnerEvent, NewMessageEvent, ChatChangedEvent

from funpayhub.lib.telegram.ui import UIRegistry

from funpayhub.app.formatters import (
    NewMessageContext,
    GeneralFormattersCategory,
    MessageFormattersCategory,
)
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.app.telegram.main import Telegram
from funpayhub.app.funpay.filters import is_fph_command
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import NewMessageMenuContext


if TYPE_CHECKING:
    from funpaybotengine import Bot
    from funpaybotengine.types import Message

    from funpayhub.lib.hub.text_formatters import FormattersRegistry

    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.properties.auto_response import AutoResponseEntryProperties


on_new_message_router = r = Router(name='fph:on_new_message_router')


@r.on_new_message(is_fph_command, handler_id='fph:process_command')
async def process_command(
    event: NewMessageEvent,
    fp_formatters: FormattersRegistry,
    fp_bot: Bot,
    command: AutoResponseEntryProperties,
) -> None:
    """
    Хэндлер ищет команду в списке команд и выполняет ее.
    """
    command = command

    if command.reply.value:
        text = await fp_formatters.format_text(
            text=command.response_text.value,
            query=GeneralFormattersCategory.or_(MessageFormattersCategory),
            context=NewMessageContext(new_message_event=event),
            raise_on_error=not command.ignore_formatters_errors.value,
        )

        await text.send(bot=fp_bot, chat_id=event.message.chat_id)


@r.on_chat_changed(handler_id='fph:new_message_notification')
async def send_new_message_notification(
    event: ChatChangedEvent,
    events_stack: list[RunnerEvent],
    tg: Telegram,
    tg_ui: UIRegistry,
    data: dict[str, Any],
    properties: FunPayHubProperties,
    fp: FunPay,
) -> None:
    msgs: list[Message] = []
    appearance_props = properties.telegram.appearance.new_message_appearance

    for i in events_stack:
        if i.name != NewMessageEvent.__event_name__ or i.message.chat_id != event.chat_preview.id:
            continue

        if fp.is_manual_message(i.message.id) and not appearance_props.show_mine_from_hub.value:
            continue
        elif await i.message.is_sent_by_bot() and not appearance_props.show_automatic.value:
            continue
        elif i.message.from_me and not appearance_props.show_mine.value:
            continue
        msgs.append(i.message)

    if not msgs:
        return

    only_mine = True
    only_automatic = True
    only_mine_from_hub = True

    for i in msgs:
        is_manual = fp.is_manual_message(i.id)
        by_bot = await i.is_sent_by_bot()
        automatic = (not is_manual) and by_bot

        only_mine &= i.from_me and not is_manual and not by_bot
        only_mine_from_hub &= is_manual
        only_automatic &= automatic

    print(f'{only_mine=}, {only_automatic=}, {only_mine_from_hub=}')

    if any(
        [
            only_mine and not appearance_props.show_if_mine_only.value,
            only_automatic and not appearance_props.show_automatic_only.value,
            only_mine_from_hub and not appearance_props.show_mine_from_hub_only.value,
        ],
    ):
        return

    context = NewMessageMenuContext(
        chat_id=-1,  # todo
        menu_id=MenuIds.new_funpay_message,
        funpay_chat_id=event.chat_preview.id,
        funpay_chat_name=event.chat_preview.username,
        messages=msgs,
    )
    menu = await tg_ui.build_menu(context, data)

    await tg.send_notification(
        'new_message',
        text=menu.total_text,
        reply_markup=menu.total_keyboard(convert=True),
    )
