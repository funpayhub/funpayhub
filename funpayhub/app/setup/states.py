from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message

from funpayhub.app.telegram.states import State
from funpayhub.lib.telegram.callback_data import CallbackData


@dataclass
class EnteringProxyState(State, identifier='EnteringProxyState'):
    message: Message
    callback_data: CallbackData
    last_entered_proxy: str | None = ''


@dataclass
class EnteringUserAgentState(State, identifier='EnteringUserAgentState'):
    message: Message
    callback_data: CallbackData
