from __future__ import annotations


__all__ = [
    'Hook',
    'HookArg',
    'HooksRegistry'
]


from dataclasses import dataclass
from typing_extensions import Any
from collections.abc import Callable
from eventry.asyncio.callable_wrappers import CallableWrapper


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




@dataclass
class Hook:
    id: str
    """ID хука."""

    name: str
    """Человеко-читаемое название хука."""

    description: str
    """Описание хука."""

    callable: Callable[..., Any] | CallableWrapper[Any]
    """Функция хука."""

    args: tuple[HookArg, ...] = ()
    """Принимаемые аргументы хука."""

    filter: Callable[..., Any] | CallableWrapper[Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.callable, CallableWrapper):
            self.callable = CallableWrapper(self.callable)

        if self.filter is not None and not isinstance(self.filter, CallableWrapper):
            self.filter = CallableWrapper(self.filter)


class HooksRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, Hook] = {}

    def add_hook(self, hook: Hook, overwrite: bool = False) -> None:
        if hook.id in self._hooks and not overwrite:
            raise ValueError(f"Hook {hook.id!r} already exists.")

        self._hooks[hook.id] = hook
