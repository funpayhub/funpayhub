from __future__ import annotations

import re


def get_bought_amount(offer_name: str, order_title: str) -> int:
    """
    Сопоставляет название лота с названием заказа.

    Если в названии заказа есть название лота, возвращает купленное кол-во.
    В противном случае - возвращает 0.
    """
    offer_name = re.escape(offer_name)
    match = re.search(
        rf'(^|(,\s+))(?P<offername>{offer_name})($|\.$|(,\s+)).+(?P<amount>\d+ (шт|pcs)\.?,?)?.+',
        order_title,
    )
    if not match:
        return 0

    return int(match.group('amount')) if match.group('amount') else 1
