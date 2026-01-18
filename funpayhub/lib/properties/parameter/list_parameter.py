from __future__ import annotations


__all__ = ['ListParameter']

from typing import Any
from contextlib import suppress
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
        default_factory: Callable[[], list[ItemType]],
        validator: Callable[[list[ItemType]], Awaitable[None]] | _UNSET = UNSET,
        flags: Iterable[Any] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            default_factory=default_factory,
            validator=validator,
            converter=lambda _: _,
            flags=flags,
        )

    async def add_item(self, item: ItemType, save: bool = True) -> None:
        self.value.append(item)
        if save:
            await self.save()

    async def pop_item(self, index: int, save: bool = True) -> ItemType:
        result = self.value.pop(index)
        if save:
            await self.save()
        return result

    async def remove_item(self, item: ItemType, save: bool = True) -> None:
        with suppress(ValueError):
            self.value.remove(item)
            if save:
                await self.save()
