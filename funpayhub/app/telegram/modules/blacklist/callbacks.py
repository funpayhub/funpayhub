from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class BlockUser(CallbackData, identifier='add_user_to_blacklist'): ...


class DeleteUser(CallbackData, identifier='delete_user_from_blacklist'):
    username: str
