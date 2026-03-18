from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData
from funpayhub.lib.base_app.telegram.app.ui.callbacks import Pageable


class OpenAddAutoDeliveryRuleMenu(CallbackData, identifier='open_add_ad_rule_menu'): ...


class AddAutoDeliveryRule(CallbackData, identifier='add_ad_rule'):
    rule: str


class DeleteAutoDeliveryRule(CallbackData, identifier='delete_ad_rule'):
    rule: str


class OpenBindGoodsMenu(CallbackData, identifier='open_bind_goods_menu'):
    rule: str


class BindGoodsSourceToAutoDelivery(CallbackData, Pageable, identifier='bind_goods_source_to_ad'):
    rule: str
    source_id: str
