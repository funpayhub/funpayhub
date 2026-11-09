from __future__ import annotations


__all__ = [
    'CheckForUpdates',
    'DownloadUpdate',
    'InstallUpdate',
]


from dothub.lib.telegram.callback_data import CallbackData


class CheckForUpdates(CallbackData, identifier='check_for_updates'):
    pass


class DownloadUpdate(CallbackData, identifier='download_update'):
    url: str


class InstallUpdate(CallbackData, identifier='install_update'):
    instance_id: str
