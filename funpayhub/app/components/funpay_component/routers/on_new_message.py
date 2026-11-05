from __future__ import annotations

from typing import TYPE_CHECKING, Any

from funpaybotengine import Router
from funpaybotengine.types import Message
from funpaybotengine.runner import EventsPack
from hubplatform.expressions.manager import ExpressionsManager
from funpaybotengine.dispatching.events import NewMessage, ChatChanged

from funpayhub.app.components.telegram_component import TelegramProperties

from ..expressions import FunPayMessageContext
from ..properties.auto_response import CommandNode
from ..extensions.telegram.new_message_ui.ui import NewFunPayMessageMenuContext
from ..extensions.telegram.new_message_ui.menu_ids import NewFunPayMessageUIMenuIDs


if TYPE_CHECKING:
    from funpayhub.app.components.funpay_component import FunPayComponent, FunPayProperties
    from funpayhub.app.components.telegram_component import TelegramComponent


router = Router(name='app:on_new_message')


@router.on_chat_changed(name='app:new_message_notification')
async def send_new_message_notification(
    event: ChatChanged,
    events_pack: EventsPack,
    telegram_component: TelegramComponent,
    telegram_properties: TelegramProperties,
    funpay_component: FunPayComponent,
) -> None:
    print('NEW MESSAGE')
    msgs: list[Message] = []
    appearance_props = telegram_properties.appearance.new_message_appearance

    automatic_msgs: set[int] = set()
    manual_msgs: set[int] = set()

    for i in events_pack.events:
        if not isinstance(i, NewMessage) or i.message.chat_id != event.chat_preview.id:
            continue

        through_app = await funpay_component.is_sent_through_app(i.message.id)
        automatic = await funpay_component.is_automatic_message(i.message.id)
        manual = through_app and not automatic
        if automatic_msgs:
            automatic_msgs.add(i.message.id)
        if manual:
            manual_msgs.add(i.message.id)

        if manual and not appearance_props.show_mine_from_hub.value:
            continue
        if automatic and not appearance_props.show_automatic.value:
            continue
        if i.message.from_me and not appearance_props.show_mine.value:
            continue
        msgs.append(i.message)

    if not msgs:
        return

    only_mine = True
    only_automatic = True
    only_mine_from_hub = True

    for i in msgs:
        manual = i.id in manual_msgs
        automatic = i.id in automatic_msgs

        only_mine &= i.from_me and not manual and not automatic
        only_mine_from_hub &= manual
        only_automatic &= automatic

    if any(
        [
            only_mine and not appearance_props.show_if_mine_only.value,
            only_automatic and not appearance_props.show_automatic_only.value,
            only_mine_from_hub and not appearance_props.show_mine_from_hub_only.value,
        ],
    ):
        return

    telegram_component.send_menu_notification(
        menu_id=NewFunPayMessageUIMenuIDs.new_message,
        menu_context=NewFunPayMessageMenuContext(
            funpay_chat_name=event.chat_preview.username,
            funpay_chat_id=event.chat_preview.id,
            messages=msgs,
        ),
        notifications_channel_path=['funpay', 'new_message'],
    )


async def command_filter(
    event: NewMessage,
    funpay_props: FunPayProperties,
) -> dict[str, Any] | bool:
    if event.message.sender_id in [0, 500]:
        return False

    if not event.message.text or event.message.text not in funpay_props.auto_response.subnodes:
        return False

    node = funpay_props.auto_response.get_command_node(event.message.text)

    if event.message.from_me and not node.react_on_me.value:
        return False
    if not event.message.from_me and not node.react_on_others:
        return False
    if not node.reply.value:
        return False
    return {'command_node': node}


@router.on_new_message(command_filter, name='app:funpay_component:run_command')
async def run_command(
    event: NewMessage,
    command_node: CommandNode,
    expressions_manager: ExpressionsManager,
):
    context = FunPayMessageContext(
        marketplace_id='funpay',
        initiator_id=str(event.message.sender_id),
        initiator_username=str(event.message.sender_username),
        message_id=str(event.message.id),
        message_text=str(event.message.text),
        funpay_message_obj=event.message,
    )

    result = await expressions_manager.format_string(
        string=command_node.response_text.value,
        context=context,
        ignore_errors=command_node.ignore_expression_errors.value,
    )

    event['app:funpay_component:auto_response:generated_response'] = result

    try:
        event['app:funpay_component:auto_response:sent_response'] = await event.message.reply(
            result.result_text,
        )
    except Exception as e:
        event['app:funpay_component:auto_response:error'] = e
        # todo: logging, notification
