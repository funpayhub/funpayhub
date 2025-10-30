from __future__ import annotations


__all__ = ['classproperty']


from typing import Any
from collections.abc import Callable


class classproperty[T, R]:
    def __init__(self, func: Callable[[type[T]], R]) -> None:
        self.func = func

    def __get__(self, obj: Any, cls: type[T]) -> R:
        return self.func(cls)
