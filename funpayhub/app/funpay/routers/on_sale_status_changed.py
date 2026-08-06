from __future__ import annotations

from typing import TYPE_CHECKING

from funpaybotengine import Router
from funpaybotengine.dispatching import SaleStatusChangedEvent
from funpaybotengine.types.enums import OrderStatus
from funpaybotengine.dispatching.filters import FinalOrderStatusFilter, all_of

from funpayhub.app.telegram.main import Telegram
from funpayhub.app.telegram.ui.builders.context import SaleClosedNotificationMenuContext
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.notification_channels import NotificationChannels
from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.loggers import main as logger

from funpayhub.lib.translater import (
    en as _en,
    translater,
)
from funpayhub.lib.hub.text_formatters.category import InCategory

from funpayhub.app.formatters import (
    NewOrderContext,
    OrderFormattersCategory,
    GeneralFormattersCategory,
)


if TYPE_CHECKING:
    from funpayhub.lib.hub.text_formatters import FormattersRegistry

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties as FPHProps


on_sale_status_change = r = Router(name='fph:on_sale_status_changed')
ru = translater.translate


@r.on_sale_closed(
    all_of(
        FinalOrderStatusFilter(OrderStatus.COMPLETED),
        lambda properties: properties.on_sale_confirmation.reply_in_chat.value
        and properties.on_sale_confirmation.response_text.value,
    ),
)
async def send_order_confirmation_message(
    event: SaleStatusChangedEvent,
    properties: FPHProps,
    fp_formatters: FormattersRegistry,
    hub: FunPayHub,
) -> None:
    try:
        messages_pack = await fp_formatters.format_text(
            properties.on_sale_confirmation.response_text.value,
            context=NewOrderContext(
                new_message_event=event.related_new_message_event,
                order_event=event,
                goods_to_deliver=[],
            ),
            query=InCategory(OrderFormattersCategory).or_(InCategory(GeneralFormattersCategory)),
        )
    except Exception as e:
        logger.error(_en('Confirmation message formatting error.'), exc_info=True)
        hub.telegram.send_error_notification(
            ru('<b>❌ Ошибка форматирования сообщения ответа на подтверждение заказа.</b>'),
            e,
        )
        return

    try:
        await hub.funpay.send_messages_stack(
            messages_pack,
            chat_id=event.message.chat_id,
        )
    except Exception as e:
        logger.error(_en('Confirmation message sending error.'), exc_info=True)
        hub.telegram.send_error_notification(
            ru('<b>❌ Ошибка отправления ответа на подтверждение заказа.</b>'),
            e,
        )

@r.on_sale_closed(FinalOrderStatusFilter(OrderStatus.COMPLETED))
async def send_closed_notification(event: SaleStatusChangedEvent, tg: Telegram, tg_ui: UIRegistry):
    menu = await SaleClosedNotificationMenuContext(
        menu_id=MenuIds.sale_closed_notification,
        chat_id=-1,
        sale_event=event,
    ).build_menu(tg_ui)
    tg.send_notification(NotificationChannels.SALE_STATUS_CHANGED, **menu)

