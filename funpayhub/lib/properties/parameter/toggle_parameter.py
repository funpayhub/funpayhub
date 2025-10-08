from __future__ import annotations

from typing import Any
from collections.abc import Callable, Awaitable, Iterable

from funpayhub.lib.properties.base import UNSET, _UNSET
from funpayhub.lib.properties.parameter.base import MutableParameter
from funpayhub.lib.properties.parameter.converters import bool_converter


class ToggleParameter(MutableParameter[bool]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        default_value: bool,
        validator: Callable[[bool], Awaitable[None]] | _UNSET = UNSET,
        flags: Iterable[Any] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            validator=validator,
            converter=bool_converter,
            flags=flags,
        )

    async def on(self, save: bool = True) -> None:
        await self.set_value(True, skip_converter=True, save=save)

    async def off(self, save: bool = True) -> None:
        await self.set_value(False, skip_converter=True, save=save)

    async def toggle(self, save: bool = True) -> None:
        await self.set_value(not self.value, skip_converter=True, save=save)

    async def next_value(self, save: bool = True) -> bool:
        await self.toggle(save=save)
        return self.value
