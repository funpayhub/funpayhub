from __future__ import annotations

from typing import TYPE_CHECKING

from funpaybotengine import Router
from funpaybotengine.types import Message
from funpaybotengine.runner import EventsPack
from funpaybotengine.dispatching.events import NewMessage, ChatChanged

from funpayhub.app.components.telegram_component import TelegramProperties

from ..extensions.telegram.new_message_ui.ui import NewFunPayMessageMenuContext
from ..extensions.telegram.new_message_ui.menu_ids import NewFunPayMessageUIMenuIDs


if TYPE_CHECKING:
    from funpayhub.app.components.funpay_component import FunPayComponent
    from funpayhub.app.components.telegram_component import TelegramComponent


router = Router(name='app:on_new_message')


@router.on_chat_changed(name='fph:new_message_notification')
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
