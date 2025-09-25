from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class SendExecFile(CallbackData, identifier='send_exec_file'):
    exec_id: str
