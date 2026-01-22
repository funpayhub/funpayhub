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
    """ID текущего запуска."""

    step: str
    """Выполненый этап установки."""

    action: int
    """Выбранный вариант для этапа."""

    lang: str | None = None
    """Выбранный язык. Используется только для первого этапа (`Steps.language`)."""
