from dataclasses import dataclass
from collections.abc import Callable, Awaitable
from eventry.asyncio.callable_wrappers import CallableWrapper
from .parser import extract_calls
from typing import Any


@dataclass
class Formatter:
    key: str
    name: str
    description: str
    formatter: Callable[..., Awaitable[str] | str] | CallableWrapper[str]

    def __post_init__(self) -> None:
        if not isinstance(self.formatter, CallableWrapper):
            self.formatter = CallableWrapper(self.formatter)

    async def execute(self, user_passed_args: list[Any], data: dict[str, Any]) -> str:
        return await self.formatter(user_passed_args, data)


class FormattersRegistry:
    def __init__(self) -> None:
        self._formatters: dict[str, Formatter] = {}

    def add_formatter(self, formatter: Formatter, raise_if_exists: bool = True) -> None:
        if raise_if_exists and formatter.key in self._formatters:
            raise ValueError(f'Formatter with key {formatter.key} already exists.')

        self._formatters[formatter.key] = formatter

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, str):
            return item in self._formatters

        elif isinstance(item, Formatter):
            return item.key in self._formatters
        return False

    def __getitem__(self, item: Any) -> Formatter:
        return self._formatters[item]

    def __setitem__(self, key: str, value: Formatter) -> None:
        if not isinstance(key, str):
            raise ValueError(f'Formatter key should be a str.')
        if not isinstance(value, Formatter):
            raise ValueError(f'Value should be a Formatter.')

        if key != value.key:
            raise ValueError(f'Passed key should be equals to formatters key.')

        self.add_formatter(formatter=value, raise_if_exists=False)

    async def format_text(self, text: str, data: dict[str, Any]) -> str:

        ...
