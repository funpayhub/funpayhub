from __future__ import annotations


__all__ = [
    'TranslatableException',
    'FunPayHubError',
]

from typing import Any

from funpayhub.lib.translater import formatter


class TranslatableException(Exception):
    def __init__(self, message: str, *args: Any) -> None:
        super().__init__(message, *args)
        self.message = message
        self.args = args

    def __str__(self) -> str:
        return formatter.format(self.message, self.args)

    def format_args(self, text: str) -> str:
        return formatter.format(text, self.args)


class FunPayHubError(TranslatableException):
    pass
