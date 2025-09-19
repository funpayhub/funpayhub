from __future__ import annotations


__all__ = ['ChoiceParameter', 'Item']


from typing import TYPE_CHECKING, Any, Union, Generic, TypeVar
from dataclasses import dataclass
from collections.abc import Callable

from funpayhub.lib.properties.parameter.base import CallableValue, MutableParameter
from funpayhub.lib.properties.base import _UNSET, _UNSET_TYPE
from funpayhub.lib.properties.parameter.converters import int_converter


if TYPE_CHECKING:
    from ..properties import Properties


T = TypeVar('T', bound=Any)


@dataclass(frozen=True)
class Item(Generic[T]):
    name: str
    value: T

    def __str__(self) -> str:
        return self.name


class ChoiceParameter(MutableParameter[int], Generic[T]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        choices: tuple[Union[T, Item[T]], ...],
        default_value: CallableValue[int],
        value: CallableValue[int] | _UNSET_TYPE = _UNSET,
        validator: Callable[[int], Any] | _UNSET_TYPE = _UNSET,
    ) -> None:
        self._choices: tuple[Union[T, Item[T]], ...] = choices

        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            value=value,
            validator=self._validator_factory(validator),
            converter=int_converter,
        )

    @property
    def choices(self) -> tuple[Union[T, Item[T]], ...]:
        return self._choices

    @property
    def real_value(self) -> T:
        result = self.choices[self.value]
        if isinstance(result, Item):
            return result.value
        return result

    def _validator_factory(
        self,
        validator: Callable[[int], Any] | _UNSET_TYPE,
    ) -> Callable[[int], None]:
        def real_validator(value: int) -> None:
            if value > len(self.choices) - 1:
                raise ValueError('Index out of range!')  # todo: validation text
            if not isinstance(validator, _UNSET_TYPE):
                validator(value)

        return real_validator

    def __next__(self) -> T:
        if len(self.choices) == self.value+1:
            self.set_value(0, save=True)
            return self.real_value

        self.set_value(self.value + 1, save=True)
        return self.real_value
