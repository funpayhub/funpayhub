from __future__ import annotations

from typing import Any, TYPE_CHECKING
from collections.abc import Callable

from .base import _UNSET, _UNSET_TYPE, CallableValue, MutableParameter


if TYPE_CHECKING:
    from ..properties import Properties


class ListParameter(MutableParameter[list[Any]]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        default_value: CallableValue[list[Any]],
        value: CallableValue[list[Any]] | _UNSET_TYPE = _UNSET,
        validator: Callable[[Any], list[Any]] | _UNSET_TYPE = _UNSET,
    ) -> None:
        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            value=value,
            validator=validator,
            converter=list,
        )
