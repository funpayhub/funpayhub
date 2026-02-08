from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from funpaybotengine import Router
from funpaybotengine.dispatching.filters import all_of

from funpayhub.lib.exceptions import NotEnoughGoodsError


if TYPE_CHECKING:
    from funpaybotengine.dispatching.events import NewSaleEvent

    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.hub.text_formatters import FormattersRegistry

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

    for i in properties.auto_delivery.entries:
        pattern = _offer_name_re_factory(i)
        if pattern.search(order.title):
            props = i
            break
    else:
        return False

    if not props.auto_delivery.value or not props.delivery_text.value:
        return False

    return {'auto_delivery': props}


@router.on_new_sale(
    all_of(
        lambda properties: properties.toggles.auto_delivery.value,
        auto_delivery_enabled_filter,
    )
)
async def deliver_goods(
    event: NewSaleEvent,
    auto_delivery: AutoDeliveryEntryProperties,
    goods_manager: GoodsSourcesManager,
    fp_formatters: FormattersRegistry,
):
    order = await event.get_order_preview()
    amount = 1
    if auto_delivery.multi_delivery.value and auto_delivery.goods_source.value:
        match = PCS_RE.search(order.title)
        amount = int(match.group()) if match else 1

    try:
        goods = await goods_manager.pop_goods(auto_delivery.goods_source.value, amount)
    except KeyError:
        return False  # todo logging, notification
    except NotEnoughGoodsError:
        return False  # todo logging, notification

    fp_formatters
