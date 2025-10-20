from __future__ import annotations


__all__ = ['ListParameter']


from typing import Any
from collections.abc import Callable, Iterable, Awaitable

from funpayhub.lib.properties.base import UNSET, _UNSET
from funpayhub.lib.properties.parameter.base import MutableParameter


ALLOWED_TYPES = int | float | bool | str


class ListParameter[ItemType: ALLOWED_TYPES](MutableParameter[list[ItemType]]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        default_value: list[ItemType],
        validator: Callable[[list[ItemType]], Awaitable[None]] | _UNSET = UNSET,
        flags: Iterable[Any] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            validator=validator,
            converter=lambda _: _,
            flags=flags,
        )

    async def add_item(self, item: ItemType) -> None:
        self.value.append(item)

    async def pop_item(self, index: int) -> ItemType:
        return self.value.pop(index)

    async def remove_item(self, item: ItemType) -> None:
        return self.value.remove(item)
