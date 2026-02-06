from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData
from funpayhub.lib.base_app.telegram.app.ui.callbacks import Pageable


class ToggleNotificationChannel(CallbackData, identifier='toggle_notification_channel'):
    channel: str


# New message menu
class SendMessage(CallbackData, Pageable, identifier='sm'):
    to: int | str
    name: str


class SendTemplate(CallbackData, identifier='st'):
    to: int | str
    index: int


class MuteChat(CallbackData, identifier='mute_chat'):
    chat_id: int | str


# Other
class ShutDown(CallbackData, identifier='shutdown'):
    exit_code: int


# Autodelivery
class OpenAddAutoDeliveryRuleMenu(CallbackData, identifier='open_add_autodelivery_rule_menu'): ...


class AddAutoDeliveryRule(CallbackData, identifier='add_autodelivery_rule'):
    rule: str


class DeleteAutoDeliveryRule(CallbackData, identifier='delete_autodelivery_rule'):
    rule: str


class AutoDeliveryOpenGoodsSourcesList(
    CallbackData,
    identifier='auto_delivery_optn_goods_sources_list',
):
    rule: str


class BindGoodsSourceToAutoDelivery(
    CallbackData,
    Pageable,
    identifier='bind_goods_source_to_autodelivery',
):
    rule: str
    source_id: str
