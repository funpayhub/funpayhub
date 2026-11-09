from __future__ import annotations


__all__ = [
    'ToggleNotificationsChannel',
    'BulkChangeNotificationsCategory',
]

from hubplatform.telegram.ui import SessionCallbackData


class ToggleNotificationsChannel(SessionCallbackData, identifier='app.toggle_notifications'):
    channel_path: list[str]


class BulkChangeNotificationsCategory(
    SessionCallbackData,
    identifier='app.bulk_toggle_notifications',
):
    category_path: list[str]
    enable: bool
