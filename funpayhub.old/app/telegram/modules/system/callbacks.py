from __future__ import annotations

from dothub.lib.telegram.callback_data import CallbackData


class ShutDown(CallbackData, identifier='shutdown'):
    exit_code: int
