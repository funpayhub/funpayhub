from aiogram.utils.keyboard import CallbackData
from funpayhub.lib.telegram.callbacks import Pageable


class OpenExecRegistry(CallbackData, Pageable, prefix='open_exec_registry'):
    ...


class OpenExecCode(CallbackData, Pageable, prefix='open_exec_code'):
    exec_id: str


class OpenExecOutput(CallbackData, Pageable, prefix='open_exec_output'):
    exec_id: str


class SendExecFile(CallbackData, prefix='send_exec_file'):
    exec_id: str
