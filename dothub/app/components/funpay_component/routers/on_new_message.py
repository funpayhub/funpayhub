from __future__ import annotations

from typing import TYPE_CHECKING, Any

from funpaybotengine import Router
from funpaybotengine.types import Message, CurrentlyViewingOfferInfo
from funpaybotengine.runner import EventsPack
from funpaybotengine.types.enums import MessageType
from hubplatform.expressions.manager import ExpressionsManager
from funpaybotengine.dispatching.events import NewMessage, ChatChanged

from dothub.loggers import funpay_component as logger
from dothub.app.components.telegram_component import TelegramProperties

from ..expressions import FunPayMessageContext
from ..properties.auto_response import CommandNode
from ..extensions.telegram.new_message_ui.ui import NewFunPayMessageMenuContext
from ..extensions.telegram.new_message_ui.menu_ids import NewFunPayMessageUIMenuIDs


if TYPE_CHECKING:
    from dothub.app.components.funpay_component import FunPayComponent, FunPayProperties
    from dothub.app.components.telegram_component import TelegramComponent

    from ..first_response_cache import FirstResponseCache


router = Router(name='app:on_new_message')


@router.on_chat_changed(name='app:new_message_notification')
async def send_new_message_notification(
    event: ChatChanged,
    events_pack: EventsPack,
    telegram_component: TelegramComponent,
    telegram_properties: TelegramProperties,
    funpay_component: FunPayComponent,
) -> None:
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
    result = await expressions_manager.format_string(
        string=command_node.response_text.value,
        context=FunPayMessageContext(
            initiator_id=str(event.message.sender_id),
            initiator_username=str(event.message.sender_username),
            message_id=str(event.message.id),
            message_text=str(event.message.text),
            funpay_message_obj=event.message,
        ),
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


SYSTEM_SENDER_IDS = (0, 500)


@router.on_new_message(name='app:funpay_component:first_response')
async def send_first_response(
    event: NewMessage,
    events_pack: EventsPack,
    funpay_props: FunPayProperties,
    funpay_component: FunPayComponent,
    first_response_cache: FirstResponseCache,
    expressions_manager: ExpressionsManager,
) -> None:
    message = event.message
    chat_id = message.chat_id
    sender_id = message.sender_id
    props = funpay_props.first_response

    if not isinstance(chat_id, int):
        return
    if not props.text.value and not props.has_offer_specific:
        return

    # A chat with a new order gets no greeting: it is just marked as not new.
    has_new_order = any(
        isinstance(i, NewMessage)
        and i.message.chat_id == chat_id
        and i.message.meta.type is MessageType.NEW_ORDER
        for i in events_pack.events
    )
    from_interlocutor = (
        not message.from_me and sender_id is not None and sender_id not in SYSTEM_SENDER_IDS
    )
    if not has_new_order and not from_interlocutor:
        return

    if not await first_response_cache.is_new(chat_id, max_age=props.timeout.value):
        return

    if has_new_order:
        await first_response_cache.update(chat_id)
        return

    text = props.text.value
    if props.has_offer_specific and sender_id is not None:
        offer_id = await _get_viewing_offer_id(funpay_component, sender_id)
        offer_props = props.get_offer(offer_id) if offer_id is not None else None
        if offer_props is not None:
            text = offer_props.text.value

    if not text:
        return

    try:
        result = await expressions_manager.format_string(
            string=text,
            context=FunPayMessageContext(
                initiator_id=str(message.sender_id),
                initiator_username=str(message.sender_username),
                message_id=str(message.id),
                message_text=str(message.text),
                funpay_message_obj=message,
            ),
        )
        sent = await message.reply(result.result_text)
    except Exception:
        logger.error('Failed to send first response to chat %s.', chat_id, exc_info=True)
        return

    await funpay_component.mark_message_as_automatic(sent.id)
    await first_response_cache.update(chat_id)


async def _get_viewing_offer_id(
    funpay_component: FunPayComponent,
    user_id: int,
) -> int | str | None:
    """Returns the ID of the offer the user is currently viewing, or ``None``."""
    try:
        offer = await funpay_component.bot.get_currently_viewing_offer(user_id=user_id)
    except Exception:
        logger.error('Failed to get currently viewing offer of user %s.', user_id, exc_info=True)
        return None
    return offer.id if isinstance(offer, CurrentlyViewingOfferInfo) else None
