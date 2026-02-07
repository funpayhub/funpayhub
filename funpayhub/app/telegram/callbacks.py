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
