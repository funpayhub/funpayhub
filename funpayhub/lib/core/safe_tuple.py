from __future__ import annotations


__all__ = [
    'SafeTuple',
    'safetuple',
]
from typing import Any


class SafeTuple(tuple[Any, ...]):
    def __getitem__(self, index: int) -> Any:
        try:
            return super().__getitem__(index)
        except IndexError:
            return 'NONE'


def safetuple(*args: Any) -> SafeTuple:
    return SafeTuple(args)
