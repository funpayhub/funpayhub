from __future__ import annotations


__all__ = ['ListParameter']


from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from funpayhub.lib.properties.base import _UNSET, _UNSET_TYPE
from funpayhub.lib.properties.parameter.base import (
    CallableValue,
    MutableParameter,
)


if TYPE_CHECKING:
    from ..properties import Properties


class ListParameter(MutableParameter[list[str]]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        default_value: CallableValue[list[str]],
        value: CallableValue[list[str]] | _UNSET_TYPE = _UNSET,
        validator: Callable[[list[str]], Any] | _UNSET_TYPE = _UNSET,
        flags: set[Any] | None = None,
    ) -> None:
        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            value=value,
            validator=self._validator_factory(validator),
            converter=lambda _: _,
            flags=flags
        )

    def add(self, value: str, check_exists: bool = True, save: bool = True) -> None:
        if not isinstance(value, str):
            raise ValueError('Should be string')  # todo: exception

        if check_exists and value in self.value:
            return
        self.value.append(value)

        if save:
            self.save()

    def remove(self, value: str, save: bool = True) -> None:
        try:
            self.value.remove(value)
        except ValueError:
            return

        if save:
            self.save()

    def _validator_factory(
        self,
        validator: Callable[[list[str]], Any] | _UNSET_TYPE,
    ) -> Callable[[list[str]], None]:
        def real_validator(value: list[str]) -> None:
            if not isinstance(value, list):
                raise ValueError('Expected a list')
            for i in value:
                if not isinstance(i, str):
                    raise ValueError('Expected a string')

            if not isinstance(validator, _UNSET_TYPE):
                validator(value)

        return real_validator

    def __len__(self) -> int:
        return len(self.value)
