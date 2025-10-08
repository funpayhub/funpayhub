from __future__ import annotations


__all__ = ['ListParameter']


from typing import Any
from collections.abc import Callable, Awaitable, Iterable

from funpayhub.lib.properties.base import UNSET, _UNSET
from funpayhub.lib.properties.parameter.base import MutableParameter


SIMPLE_TYPES = int | float | bool | str
ALLOWED_TYPES = SIMPLE_TYPES | list['ALLOWED_TYPES'] | dict[SIMPLE_TYPES, 'ALLOWED_TYPES']


class ListParameter(MutableParameter[list[ALLOWED_TYPES]]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        default_value: list[ALLOWED_TYPES],
        validator: Callable[[list[ALLOWED_TYPES]], Awaitable[None]] | _UNSET = UNSET,
        flags: Iterable[Any] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            validator=validator,
            converter=lambda _: _,
            flags=flags
        )

    async def add_item(self): ...

    async def remove_item(self): ...