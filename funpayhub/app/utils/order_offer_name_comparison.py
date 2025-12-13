from __future__ import annotations

import re

from funpaybotengine.types import OfferPreview, OrderPreview


def is_valid_offer(offer: OfferPreview, order: OrderPreview) -> bool:
    offer_name = re.escape(offer.name)
    match = re.search(f'(^|(,\s+))({offer_name})($|(,\s+))', order.title)
    return bool(match)
