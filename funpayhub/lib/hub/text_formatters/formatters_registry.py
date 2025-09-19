from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass
from collections.abc import Callable, Awaitable
from eventry.asyncio.callable_wrappers import CallableWrapper

from .parser import extract_calls
from typing import Any


if TYPE_CHECKING:
    from funpaybotengine.client.bot import Bot


@dataclass
class Formatter:
    key: str
    name: str
    description: str
    formatter: Callable[..., Awaitable[str | Image] | str | Image] | CallableWrapper[str | Image]

    def __post_init__(self) -> None:
        if not isinstance(self.formatter, CallableWrapper):
            self.formatter = CallableWrapper(self.formatter)

    async def execute(self, user_passed_args: list[Any], data: dict[str, Any]) -> str:
        return await self.formatter(user_passed_args, data)



@dataclass
class Image:
    path: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.path and not self.id:
            raise ValueError('Image path or ID must be provided.')


class MessagesStack:
    def __init__(self, entries: list[str | Image]):
        self.entries = []
        for entry in entries:
            self.entries.append(entry)

        # todo: split too big messages

    async def send(self, bot: Bot, chat_id: int | str):
        for entry in self.entries:
            if isinstance(entry, str):
                await bot.send_message(chat_id=chat_id, text=entry)
            elif isinstance(entry, Image):
                await bot.send_message(chat_id=chat_id, image=entry.id or entry.path)


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

    async def format_text(self, text: str, data: dict[str, Any]) -> MessagesStack:
        parser = extract_calls(text)
        result: list[str | Image] = []
        first_iter = True

        while True:
            try:
                call_name, args, call_start, call_end = parser.send(None if first_iter else text)
                if first_iter:
                    first_iter = False
            except StopIteration:
                self.append_or_concatenate(result, text)
                return MessagesStack(result)

            self.append_or_concatenate(result, text[:call_start])
            text = text[call_end+1:]

            if call_name not in self:
                continue

            try:
                self.append_or_concatenate(result, await self[call_name].execute(args, data))
            except:
                continue

    def append_or_concatenate(self, to: list[Any], obj: Any) -> None:
        if not to:
            to.append(obj)
            return

        if isinstance(obj, str):
            if isinstance(to[-1], str):
                to[-1] += obj
            else:
                to.append(obj)
        else:
            to.append(obj)
