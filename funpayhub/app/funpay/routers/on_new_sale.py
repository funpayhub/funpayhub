from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from funpaybotengine import Router
from funpaybotengine.dispatching.filters import all_of

from loggers import main as logger

from funpayhub.lib.exceptions import NotEnoughGoodsError

from funpayhub.app.formatters import GoodsFormatter, NewOrderContext


if TYPE_CHECKING:
    from funpaybotengine.dispatching.events import NewSaleEvent

    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.hub.text_formatters import FormattersRegistry

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.app.properties.auto_delivery_properties import AutoDeliveryEntryProperties


router = Router(name='fph:on_new_sale')


PCS_RE = re.compile(r'(?:^|, )(\d+) (?:шт|pcs)\.(?:,|$)')


def _offer_name_re_factory(name: str) -> re.Pattern[str]:
    return re.compile(rf'(?:^|, )({re.escape(name)})(?:,|$)')


async def auto_delivery_enabled_filter(
    event: NewSaleEvent,
    properties: FPHProps,
) -> bool | dict[str, Any]:
    order = await event.get_order_preview()

    for k, v in properties.auto_delivery.entries.items():
        pattern = _offer_name_re_factory(k)
        if pattern.search(order.title):
            props = v
            break
    else:
        return False

    if not props.auto_delivery.value or not props.delivery_text.value:
        return False

    return {'auto_delivery': props}


class DeliverGoodsHandler:
    async def __call__(
        self,
        event: NewSaleEvent,
        auto_delivery: AutoDeliveryEntryProperties,
        goods_manager: GoodsSourcesManager,
        fp_formatters: FormattersRegistry,
        hub: FunPayHub,
    ) -> None:
        order = await event.get_order_preview()

        calls = fp_formatters.extract_calls(auto_delivery.delivery_text.value)
        if GoodsFormatter.key in calls.invocation_names:
            amount = 1
            if auto_delivery.multi_delivery.value and auto_delivery.goods_source.value:
                match = PCS_RE.search(order.title)
                amount = int(match.group()) if match else 1

            goods_source_id = auto_delivery.goods_source.value
            try:
                goods = await goods_manager.pop_goods(goods_source_id, amount)
            except KeyError:
                logger.error(
                    'Unable to issue goods for order %s: goods source %s not found.',
                    order.id,
                    goods_source_id,
                )  # todo: notification
                return
            except NotEnoughGoodsError:
                logger.error(
                    'Unable to issue goods for order %s: not enough goods in bound source %s.',
                    order.id,
                    goods_source_id,
                )  # todo: notification
                return
        else:
            goods = []

        context = NewOrderContext(
            order_event=event,
            goods_to_deliver=goods,
            new_message_event=event.related_new_message_event,
        )
        response_text = await fp_formatters.format_text(
            auto_delivery.delivery_text.value,
            context=context,
        )

        try:
            # Это очень плохо!
            # Сейчас подставляется hub, потому что у него есть такой же метод
            # send_message с такими же сигнатурами, но
            # нельзя это так оставлять!
            await response_text.send(hub.funpay, event.message.chat_id)  # todo
            return
        except Exception:
            # todo: logging
            import traceback

            print(traceback.format_exc())
            await goods_manager.add_goods(goods_source_id, goods)

    async def get_goods(self): ...


@router.on_new_sale(
    all_of(
        lambda properties: properties.toggles.auto_delivery.value,
        auto_delivery_enabled_filter,
    ),
)
async def deliver_goods():
    await DeliverGoodsHandler()()
