from __future__ import annotations


__all__ = [
    'OpenPluginInfo',
    'SetPluginStatus',
    'RemovePlugin',
    'InstallPlugin',
]


from funpayhub.lib.telegram.callback_data import CallbackData


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
