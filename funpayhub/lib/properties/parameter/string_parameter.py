from __future__ import annotations

from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from .base import _UNSET, _UNSET_TYPE, CallableValue, MutableParameter


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
        validator: Callable[[Any], str] | _UNSET_TYPE = _UNSET,
    ) -> None:
        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            value=value,
            validator=validator,
            converter=str,
        )
