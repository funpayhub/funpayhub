from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class BlockUser(CallbackData, identifier='block_user'): ...


class DeleteUser(CallbackData, identifier='delete_user'):
    username: str
