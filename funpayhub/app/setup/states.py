from funpayhub.app.telegram.states import State
from aiogram.types import Message

from funpayhub.lib.telegram.callback_data import CallbackData
from dataclasses import dataclass


@dataclass
class EnteringProxyState(State, identifier='EnteringProxyState'):
    message: Message
    callback_data: CallbackData
