from __future__ import annotations

from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from funpayhub.lib.properties.base import _UNSET, _UNSET_TYPE
from funpayhub.lib.properties.parameter.base import CallableValue, MutableParameter
from funpayhub.lib.properties.parameter.converters import string_converter


if TYPE_CHECKING:
    from ..properties import Properties


class StringParameter(MutableParameter[str]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        default_value: CallableValue[str],
        value: CallableValue[str] | _UNSET_TYPE = _UNSET,
        validator: Callable[[str], str] | _UNSET_TYPE = _UNSET,
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
            converter=string_converter,
            flags=flags
        )
