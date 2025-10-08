from __future__ import annotations

from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from typing_extensions import Self

from funpayhub.lib.properties.base import UNSET, _UNSET
from funpayhub.lib.properties.parameter.base import CallableValue, MutableParameter
from funpayhub.lib.properties.parameter.converters import bool_converter


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
        value: CallableValue[bool] | _UNSET = UNSET,
        validator: Callable[[bool], Any] | _UNSET = UNSET,
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
            converter=bool_converter,
            flags=flags,
        )

    def on(self, save: bool = True) -> Self:
        return self.set_value(True, skip_converter=True, save=save)

    def off(self, save: bool = True) -> Self:
        return self.set_value(False, skip_converter=True, save=save)

    def toggle(self, save: bool = True) -> Self:
        return self.set_value(not self.value, skip_converter=True, save=save)

    def __next__(self) -> bool:
        # todo: delete
        self.toggle(save=True)
        return self.value

    def next_value(self, save: bool = True) -> bool:
        self.toggle(save=save)
        return self.value