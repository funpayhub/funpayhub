from __future__ import annotations


__all__ = ['TranslatableException']


class TranslatableException(Exception):
    def __init__(self, message: str, *args) -> None:
        super().__init__(message, *args)
        self.message = message
        self.args = args

    def __str__(self) -> str:
        return self.message % self.args

    def format_args(self, text: str) -> str:
        return text % self.args
