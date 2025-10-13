from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload
from dataclasses import dataclass
from collections.abc import Callable, Awaitable

from eventry.asyncio.callable_wrappers import CallableWrapper

from .parser import extract_calls


if TYPE_CHECKING:
    from funpaybotengine.client.bot import Bot


type FORMATTER_R = str | Image | list[str | Image]


@dataclass
class Formatter:
    """
    Класс, описывающий форматтер.
    """

    key: str
    """Ключ форматтера. Используется в тексте в виде `$ключ`."""

    name: str
    """Человеко-читаемое название форматтера."""

    description: str
    """Описание форматтера, документация и т.д."""

    formatter: Callable[..., Awaitable[FORMATTER_R] | FORMATTER_R] | CallableWrapper[FORMATTER_R]
    """
    Функция-форматтер.
    Должна возвращать текст или объект `Image`.
    """

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
        self.entries = entries

    async def send(self, bot: Bot, chat_id: int | str):
        for entry in self.entries:
            if isinstance(entry, str):
                await bot.send_message(chat_id=chat_id, text=entry)
            elif isinstance(entry, Image):
                await bot.send_message(chat_id=chat_id, image=entry.id or entry.path)


class FormattersRegistry:
    def __init__(self) -> None:
        """
        Реестр форматтеров.
        """
        self._formatters: dict[str, Formatter] = {}

    def add_formatter(self, formatter: Formatter, raise_if_exists: bool = True) -> None:
        """
        Добавляет форматтер в реестр.

        :param formatter: Объект форматтера.
        :param raise_if_exists: Возбуждать ли `ValueError`, если форматтер с таким же `key` уже
            существует в реестре.
        """
        if raise_if_exists and formatter.key in self._formatters:
            raise ValueError(f'Formatter with key {formatter.key} already exists.')

        self._formatters[formatter.key] = formatter

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, str):
            return item in self._formatters

        if isinstance(item, Formatter):
            return item.key in self._formatters
        return False

    @overload
    def __getitem__(self, key: str) -> Formatter: ...

    @overload
    def __getitem__(self, key: int) -> Formatter: ...

    @overload
    def __getitem__(self, key: slice) -> list[Formatter]: ...

    def __getitem__(self, item: str | int | slice) -> Formatter | list[Formatter]:
        if isinstance(item, str):
            return self._formatters[item]

        if isinstance(item, (int, slice)):
            return list(self._formatters.values())[item]

        raise TypeError(
            f'Invalid key type: expected str, int, or slice, got {type(item).__name__}.'
        )

    def __setitem__(self, key: str, value: Formatter) -> None:
        if not isinstance(key, str):
            raise ValueError(f'Invalid key type: expected str, got {type(key).__name__}.')
        if not isinstance(value, Formatter):
            raise ValueError(
                f'Invalid value type: expected Formatter, got {type(value).__name__}.',
            )

        if key != value.key:
            raise ValueError(
                f'Mismatched keys: provided mapping key {key!r} does not match '
                f'Formatter.key {value.key!r}.',
            )

        self.add_formatter(formatter=value, raise_if_exists=False)

    def __len__(self) -> int:
        return len(self._formatters)

    async def format_text(
        self,
        text: str,
        data: dict[str, Any],
        raise_on_error: bool = True,
    ) -> MessagesStack:
        """
        Извлекает из переданного текста все вызовы форматтеров и выполняет их.

        :param text: Исходный текст.
        :param data: Словарь с данными, который будет передаваться в функции-форматтеры.
        :return: `MessagesStack`.
        """
        parser = extract_calls(text)
        result: list[str | Image] = []
        first_iter = True

        while True:
            try:
                call_name, args, call_start, call_end = parser.send(None if first_iter else text)
                if first_iter:
                    first_iter = False
            except StopIteration:
                append_or_concatenate(result, text)
                return MessagesStack(result)

            append_or_concatenate(result, text[:call_start])
            text = text[call_end + 1 :]

            if call_name not in self:
                continue

            try:
                append_or_concatenate(result, await self[call_name].execute(args, data))
            except:
                if raise_on_error:
                    raise
                continue


def append_or_concatenate(to: list[Any], obj: FORMATTER_R) -> None:
    if not to or isinstance(obj, list):
        to.append(obj) if not isinstance(obj, list) else to.extend(obj)
        return

    if isinstance(obj, str):
        if isinstance(to[-1], str):
            to[-1] += obj
        else:
            to.append(obj)
    else:
        to.append(obj)
