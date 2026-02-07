from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class ShutDown(CallbackData, identifier='shutdown'):
    exit_code: int
