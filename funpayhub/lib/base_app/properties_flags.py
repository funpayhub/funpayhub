from __future__ import annotations

from enum import auto


class ParameterFlags:
    HIDE = auto()
    """Параметры с данным флагом не отображаются в меню параметров."""

    HIDE_VALUE = auto()
    """Значения параметров с данным флагом не отображаются в меню параметров."""

    PROTECT_VALUE = auto()
    """Значения параметров с данным флагом замаскированы в меню параметров."""

    NEED_RESTART = auto()
    """
    После изменения значения параметра с данным флагом пользователь получит сообщение о том,
    что FunPay Hub необходимо перезапустить.
    """


class PropertiesFlags:
    HIDE = auto()


class TelegramUIEmojiFlag:
    def __init__(self, emoji: str) -> None:
        self._emoji = emoji

    @property
    def emoji(self) -> str:
        return self._emoji

    def __eq__(self, o: object) -> bool:
        if isinstance(o, type) and issubclass(o, TelegramUIEmojiFlag):
            return True
        if isinstance(o, TelegramUIEmojiFlag):
            return self.emoji == o.emoji
        if isinstance(o, str):
            return self.emoji == o
        return False

    def __hash__(self) -> int:
        return id(self)
