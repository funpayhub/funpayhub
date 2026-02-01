from __future__ import annotations

from typing import Any
from collections.abc import Callable, Iterable, Awaitable

from funpayhub.lib.properties.parameter.base import MutableParameter
from funpayhub.lib.properties.parameter.converters import int_converter


class IntParameter(MutableParameter[int]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        default_value: int,
        validator: Callable[[int], Awaitable[None]] | type[Ellipsis] = ...,
        flags: Iterable[Any] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            validator=validator,
            converter=int_converter,
            flags=flags,
        )
