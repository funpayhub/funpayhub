__all__ = [
    'TranslatableException',
    'FunPayHubError'
]

from typing import Any

class _SafeTuple(tuple[Any, ...]):
    def __getitem__(self, index: int) -> Any:
        try:
            return super().__getitem__(index)
        except IndexError:
            return '%!%'


class TranslatableException(Exception):
    def __init__(self, message: str, *args: Any) -> None:
        super().__init__(message, *args)
        self.message = message
        self.args = args

    def __str__(self) -> str:
        args = _SafeTuple(self.args)
        return self.message % args

    def format_args(self, text: str) -> str:
        return text % self.args


class FunPayHubError(TranslatableException):
    pass

