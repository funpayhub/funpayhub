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
    def __init__(self, emoji: str, premium_emoji_id: str | None = None) -> None:
        self._emoji = emoji
        self._premium_emoji_id = premium_emoji_id

    @property
    def emoji(self) -> str:
        return self._emoji

    @property
    def premium_emoji_id(self) -> str:
        return self._premium_emoji_id

    def __eq__(self, o: object) -> bool:
        if isinstance(o, type) and issubclass(o, TelegramUIEmojiFlag):
            return True
        if isinstance(o, TelegramUIEmojiFlag):
            return self.emoji == o.emoji and self.premium_emoji_id == o.premium_emoji_id
        if isinstance(o, str):
            return self.emoji == o or self.premium_emoji_id == o
        return False

    def __hash__(self) -> int:
        return id(self)


class TelegramToggleUIEmojiFlag:
    def __init__(
        self,
        on_emoji: tuple[str, str | None] | None = None,
        off_emoji: tuple[str, str | None] | None = None,
    ) -> None:
        self._on_emoji = (
            TelegramUIEmojiFlag(
                emoji=on_emoji[0],
                premium_emoji_id=on_emoji[1],
            )
            if on_emoji
            else None
        )

        self._off_emoji = (
            TelegramUIEmojiFlag(
                emoji=off_emoji[0],
                premium_emoji_id=off_emoji[1],
            )
            if off_emoji
            else None
        )

    @property
    def on_emoji(self) -> TelegramUIEmojiFlag:
        return self._on_emoji

    @property
    def off_emoji(self) -> TelegramUIEmojiFlag:
        return self._off_emoji

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, o: object) -> bool:
        return isinstance(o, type) and issubclass(o, TelegramUIEmojiFlag)
