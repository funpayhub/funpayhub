from __future__ import annotations

from aiogram.utils.keyboard import CallbackData


class SendExecFile(CallbackData, prefix='send_exec_file'):
    exec_id: str


class ChangeViewPage(CallbackData, prefix='exec_change_view_page'):
    page: int
