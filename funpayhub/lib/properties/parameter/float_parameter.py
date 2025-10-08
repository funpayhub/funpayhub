from __future__ import annotations

from typing import Any
from collections.abc import Callable, Awaitable, Iterable

from funpayhub.lib.properties.base import UNSET, _UNSET
from funpayhub.lib.properties.parameter.base import MutableParameter
from funpayhub.lib.properties.parameter.converters import float_converter



class FloatParameter(MutableParameter[float]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        default_value: float,
        validator: Callable[[float], Awaitable[None]] | _UNSET = UNSET,
        flags: Iterable[Any] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            validator=validator,
            converter=float_converter,
            flags=flags
        )
