from __future__ import annotations

from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from typing_extensions import Self

from .base import _UNSET, _UNSET_TYPE, CallableValue, MutableParameter
from .convertors import toggle_converter


if TYPE_CHECKING:
    from ..properties import Properties


class ToggleParameter(MutableParameter[bool]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        default_value: CallableValue[bool],
        value: CallableValue[bool] | _UNSET_TYPE = _UNSET,
        validator: Callable[[bool], Any] | _UNSET_TYPE = _UNSET,
    ) -> None:
        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            value=value,
            validator=validator,
            converter=toggle_converter,
        )

    def on(self, *, save: bool = True) -> Self:
        return self.set_value(True, skip_converter=True, save=save)

    def off(self, *, save: bool = True) -> Self:
        return self.set_value(False, skip_converter=True, save=save)

    def toggle(self, *, save: bool = True) -> Self:
        return self.set_value(not self.value, skip_converter=True, save=save)
