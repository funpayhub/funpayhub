from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from funpaybotengine import Router
from funpaybotengine.dispatching.filters import all_of

from loggers import main as logger
from funpayhub.app.notification_channels import NotificationChannels

from funpayhub.lib.exceptions import NotEnoughGoodsError, TranslatableException

from funpayhub.app.formatters import GoodsFormatter, NewOrderContext


if TYPE_CHECKING:
    from funpaybotengine.dispatching.events import NewSaleEvent

    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.hub.text_formatters import FormattersRegistry

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.app.properties.auto_delivery_properties import AutoDeliveryEntryProperties
    from funpaybotengine.types import OrderPreview
    from funpayhub.app.telegram.main import Telegram


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



class _Exception(TranslatableException):
    ...


class DeliverGoodsHandler:
    async def __call__(
        self,
        event: NewSaleEvent,
        auto_delivery: AutoDeliveryEntryProperties,
        goods_manager: GoodsSourcesManager,
        fp_formatters: FormattersRegistry,
        hub: FunPayHub,
        tg: Telegram
    ) -> None:
        order = await event.get_order_preview()
        goods_source_id = auto_delivery.goods_source.value

        calls = fp_formatters.extract_calls(auto_delivery.delivery_text.value)
        goods = []
        if GoodsFormatter.key in calls.invocation_names:
            try:
                goods = await self.get_goods(auto_delivery, order, goods_manager)
            except _Exception as e:
                logger.error(e.message, *e.args)
                event['deliver_error'] = e
                return
            except Exception as e:
                event['deliver_error'] = e
                raise

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
            # todo:
            #  Это очень плохо!
            #  Сейчас подставляется hub.funpay,
            #  потому что у него есть такой же метод send_message с такими же сигнатурами,
            #  нельзя это так оставлять!
            await response_text.send(hub.funpay, event.message.chat_id)
            event['delivered_goods'] = goods
            event['source_id'] = goods_source_id
            return
        except Exception as e:
            event['deliver_error'] = e
            if goods:
                await goods_manager.add_goods(goods_source_id, goods)
            raise

    async def get_goods(
        self,
        auto_delivery: AutoDeliveryEntryProperties,
        order: OrderPreview,
        goods_manager: GoodsSourcesManager
    ) -> list[str]:
        if not (goods_source_id := auto_delivery.goods_source.value):
            return []

        amount = 1
        if auto_delivery.multi_delivery.value:
            match = PCS_RE.search(order.title)
            amount = int(match.group()) if match else 1

        try:
            goods = await goods_manager.pop_goods(goods_source_id, amount)
        except KeyError:
            raise _Exception(
                'Unable to issue goods for order %s: goods source %s not found.',
                order.id,
                goods_source_id
            )
        except NotEnoughGoodsError:
            raise _Exception(
                'Unable to issue goods for order %s: not enough goods in bound source %s.',
                order.id,
                goods_source_id,
            )

        return goods


@router.on_new_sale(
    all_of(
        lambda properties: properties.toggles.auto_delivery.value,
        auto_delivery_enabled_filter,
    ),
)
async def deliver_goods(
    event: NewSaleEvent,
    auto_delivery: AutoDeliveryEntryProperties,
    goods_manager: GoodsSourcesManager,
    fp_formatters: FormattersRegistry,
    hub: FunPayHub,
    tg: Telegram
):
    await DeliverGoodsHandler()(event, auto_delivery, goods_manager, fp_formatters, hub, tg)


@router.on_new_sale()
async def send_notification(event: NewSaleEvent, tg: Telegram):
    text = 'Новый заказ'

    if event.data.get('delivered_goods'):
        text += '\nДоставленные товары: ...'
    elif event.data.get('deliver_error'):
        text += '\nТовары не доставлены.'
    else:
        text += '\n'

    await tg.send_notification(NotificationChannels.NEW_SALE, text=text)

    if event.data.get('deliver_error'):
        text = 'Произошла ошибка при доставке товара ...'
        await tg.send_notification(NotificationChannels.ERROR, text=text)
