from __future__ import annotations


__all__ = ['ListParameter']

from typing import Any, TYPE_CHECKING
from copy import copy
from types import EllipsisType
from collections.abc import Callable, Iterable, Awaitable

from funpayhub.lib.properties.parameter.base import MutableParameter


if TYPE_CHECKING:
    from .base import CONTAINER_ALLOWED_TYPES


class ListParameter[ItemType: CONTAINER_ALLOWED_TYPES](MutableParameter[list[ItemType]]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        default_factory: Callable[[], list[ItemType]] = list,
        validator: Callable[[list[ItemType]], Awaitable[None]] | EllipsisType = ...,
        add_item_validator: Callable[[list[ItemType], ItemType], Awaitable[None]]
        | EllipsisType = ...,
        remove_item_validator: Callable[[list[ItemType], ItemType], Awaitable[None]]
        | EllipsisType = ...,
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

        self._add_item_validator = add_item_validator
        self._remove_item_validator = remove_item_validator

    async def add_item(
        self,
        item: ItemType,
        save: bool = True,
        skip_validator: bool = False,
    ) -> None:
        async with self._changing_lock:
            if not skip_validator:
                await self.add_item_validate(item)

            self._value.append(item)
            if save:
                await self.save()

    async def pop_item(
        self,
        index: int,
        save: bool = True,
        skip_validator: bool = False,
    ) -> ItemType | None:
        if index < 0 or index >= len(self.value):
            return None

        async with self._changing_lock:
            if not skip_validator:
                item = self._value[index]
                await self.remove_item_validate(item)

            result = self._value.pop(index)
            if save:
                await self.save()
            return result

    async def remove_item(
        self,
        item: ItemType,
        save: bool = True,
        skip_validator: bool = False,
    ) -> None:
        if item not in self._value:
            return

        async with self._changing_lock:
            if not skip_validator:
                await self.remove_item_validate(item)

            self._value.remove(item)
            if save:
                await self.save()

    async def add_item_validate(self, item: ItemType) -> None:
        if not isinstance(self._add_item_validator, EllipsisType):
            await self._add_item_validator(copy(self._value), item)

    async def remove_item_validate(self, item: ItemType) -> None:
        if not isinstance(self._remove_item_validator, EllipsisType):
            await self._remove_item_validator(copy(self._value), item)

    @property
    def value(self) -> list[ItemType]:
        return copy(self._value)
