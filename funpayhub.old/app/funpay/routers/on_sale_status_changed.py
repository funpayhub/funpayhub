from __future__ import annotations

from typing import TYPE_CHECKING

from funpaybotengine import Router
from dothub.app.formatters import (
    NewOrderContext,
    OrderFormattersCategory,
    GeneralFormattersCategory,
)
from dothub.lib.translater import (
    en as _en,
    translater,
)
from funpaybotengine.dispatching import SaleStatusChangedEvent
from funpaybotengine.types.enums import OrderStatus
from funpaybotengine.dispatching.filters import FinalOrderStatusFilter, all_of
from dothub.lib.hub.text_formatters.category import InCategory

from dothub.loggers import main as logger


if TYPE_CHECKING:
    from dothub.app.main import FunPayHub
    from dothub.lib.hub.text_formatters import FormattersRegistry

    from dothub.app.properties import FunPayHubProperties as FPHProps


on_sale_status_change = r = Router(name='fph:on_sale_status_changed')
ru = translater.translate


@r.on_sale_closed(
    all_of(
        FinalOrderStatusFilter(OrderStatus.COMPLETED),
        lambda properties: (
            properties.on_sale_confirmation.reply_in_chat.value
            and properties.on_sale_confirmation.response_text.value
        ),
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
