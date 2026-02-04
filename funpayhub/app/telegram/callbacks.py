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
class AddCommand(CallbackData, identifier='add_command'):
    pass


class RemoveCommand(CallbackData, identifier='remove_command'):
    command: str


class CheckForUpdates(CallbackData, identifier='check_for_updates'):
    pass


class DownloadUpdate(CallbackData, identifier='download_update'):
    url: str


class InstallUpdate(CallbackData, identifier='install_update'):
    instance_id: str


class ShutDown(CallbackData, identifier='shutdown'):
    exit_code: int


# Plugins
class OpenPluginInfo(CallbackData, identifier='open_plugin_info'):
    plugin_id: str


class SetPluginStatus(CallbackData, identifier='set_plugin_status'):
    plugin_id: str
    status: bool


class RemovePlugin(CallbackData, identifier='remove_plugin'):
    plugin_id: str


class InstallPlugin(CallbackData, identifier='install_plugin'):
    mode: int
    """
    1 - from message
    2 - from repository
    3 - etc
    """  # todo


# Goods
class DownloadGoods(CallbackData, identifier='download_goods'):
    source_id: str


class UploadGoods(CallbackData, identifier='upload_goods'):
    source_id: str


class AddGoods(CallbackData, identifier='add_goods'):
    source_id: str


class RemoveGoods(CallbackData, identifier='remove_goods'):
    source_id: str


class RemoveGoodsSource(CallbackData, identifier='remove_goods_source'):
    source_id: str
    confirm: bool = False


class ReloadGoodsSource(CallbackData, identifier='reload_goods_source'):
    source_id: str


class AddGoodsTxtSource(CallbackData, identifier='add_goods_txt_source'): ...


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
