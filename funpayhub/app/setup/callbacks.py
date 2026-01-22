from __future__ import annotations

from enum import Enum, auto

from funpayhub.lib.telegram.callback_data import CallbackData


class Steps(Enum):
    language = auto()
    proxy = auto()
    user_agent = auto()
    golden_key = auto()


class SetupStep(CallbackData, identifier='s2'):
    instance_id: str
    step: str
    action: int
    lang: str | None = None
