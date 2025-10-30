from __future__ import annotations


__all__ = [
    'Hook',
    'HookArg',
    'HooksRegistry',
]


from typing import Type
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections.abc import Callable

from typing_extensions import Any
from eventry.asyncio.callable_wrappers import CallableWrapper
from funpayhub.lib.core import classproperty


@dataclass
class HookArg:
    name: str
    """Название аргумента."""

    desc: str
    """Описание аргумента."""

    default_value: Any = ...
    """Значение по умолчанию. Если значения по умолчанию нет - используйте `...`."""

    converter: Callable[[str], Any] | None = None
    """Конвертор параметра из строки в реальный тип."""


class Hook(ABC):
    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    async def __call__(self, **data: Any) -> str:
        wrapper = CallableWrapper(self.format)
        return await wrapper((), data)

    async def __filter_wrapped__(self, **data: Any) -> bool:
        wrapper = CallableWrapper(self.filter)
        return await wrapper((), data)

    async def filter(self, *args: Any, **kwargs: Any) -> bool:
        return True

    @abstractmethod
    async def format(self, *args: Any, **kwargs: Any) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def key(cls) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def name(cls) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def description(cls) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def args_description(cls) -> list[HookArg]: ...


class HooksRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, Type[Hook]] = {}

    def add_hook(self, hook: Type[Hook], overwrite: bool = False) -> None:
        if hook.name in self._hooks and not overwrite:
            raise ValueError(f'Hook {hook.name!r} already exists.')

        self._hooks[hook.name] = hook
