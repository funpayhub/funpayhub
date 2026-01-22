from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData
from enum import Enum, auto


class Steps(Enum):
    language = auto()
    proxy = auto()
    user_agent = auto()
    golden_key = auto()


class SetupStep(CallbackData, identifier='s2'):
    step: str
    action: int
    lang: str | None = None
