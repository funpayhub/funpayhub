from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class SendExecFile(CallbackData, identifier='send_exec_file'):
    exec_id: str


class SaveExecCode(CallbackData, identifier='save_exec_code'):
    exec_id: str
