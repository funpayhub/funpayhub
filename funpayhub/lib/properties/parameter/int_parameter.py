from __future__ import annotations

from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from funpayhub.lib.properties.base import UNSET, _UNSET
from funpayhub.lib.properties.parameter.base import CallableValue, MutableParameter
from funpayhub.lib.properties.parameter.converters import int_converter


if TYPE_CHECKING:
    from ..properties import Properties


class IntParameter(MutableParameter[int]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        default_value: CallableValue[int],
        value: CallableValue[int] | _UNSET = UNSET,
        validator: Callable[[int], int] | _UNSET = UNSET,
        flags: set[Any] | None = None,
    ) -> None:
        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            value=value,
            validator=validator,
            converter=int_converter,
            flags=flags
        )
