from funpaybotengine import Router
from funpaybotengine.dispatching.events import ChatChanged, NewMessage
from funpayhub.app.components.telegram import TelegramComponent, TelegramProperties
from funpayhub.app.components.funpay import FunPayComponent
from hubplatform.telegram.ui import UIManager
from funpaybotengine.runner import EventsPack
from funpaybotengine.types import Message



router = Router(name='app:on_new_message')



@router.on_chat_changed(handler_id='fph:new_message_notification')
async def send_new_message_notification(
    event: ChatChanged,
    events_pack: EventsPack,
    telegram_component: TelegramProperties,
    telegram_ui_manager: UIManager,
    telegram_props: TelegramProperties,
    funpay: FunPayComponent
) -> None:
    msgs: list[Message] = []
    appearance_props = properties.telegram.appearance.new_message_appearance

    for i in events_pack.events:
        if (
            not isinstance(i, NewMessage)
            or i.name != NewMessage.__event_name__
            or i.message.chat_id != event.chat_preview.id
        ):
            continue

        if fp.is_manual_message(i.message.id) and not appearance_props.show_mine_from_hub.value:
            continue
        if await i.message.is_sent_by_bot() and not appearance_props.show_automatic.value:
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
        is_manual = fp.is_manual_message(i.id)
        by_bot = await i.is_sent_by_bot()
        automatic = (not is_manual) and by_bot

        only_mine &= i.from_me and not is_manual and not by_bot
        only_mine_from_hub &= is_manual
        only_automatic &= automatic

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

    telegram_component.send_notification(
        'new_message',
        text=menu.total_text,
        reply_markup=menu.total_keyboard(convert=True),
    )
