from __future__ import annotations

from hubplatform.telegram.ui import SessionCallbackData


class OpenAddAutoDeliveryRuleMenu(SessionCallbackData, identifier='open_add_ad_rule_menu'): ...


class AddAutoDeliveryRule(SessionCallbackData, identifier='add_ad_rule'):
    rule: str


class DeleteAutoDeliveryRule(SessionCallbackData, identifier='delete_ad_rule'):
    rule: str


class OpenBindGoodsMenu(SessionCallbackData, identifier='open_bind_goods_menu'):
    rule: str


class BindGoodsSourceToAutoDelivery(SessionCallbackData, identifier='bind_goods_source_to_ad'):
    rule: str
    source_id: str
