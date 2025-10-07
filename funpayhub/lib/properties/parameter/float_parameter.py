from __future__ import annotations

from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from funpayhub.lib.properties.base import UNSET, _UNSET_TYPE
from funpayhub.lib.properties.parameter.base import CallableValue, MutableParameter
from funpayhub.lib.properties.parameter.converters import float_converter


if TYPE_CHECKING:
    from ..properties import Properties


class FloatParameter(MutableParameter[float]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        default_value: CallableValue[float],
        value: CallableValue[float] | _UNSET_TYPE = UNSET,
        validator: Callable[[float], float] | _UNSET_TYPE = UNSET,
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
            converter=float_converter,
            flags=flags
        )
