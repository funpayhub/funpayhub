from __future__ import annotations


__all__ = ['ChoiceParameter', 'Item',]


from typing import Any, TYPE_CHECKING, Generic, TypeVar
from collections.abc import Callable

from .base import _UNSET, _UNSET_TYPE, CallableValue, MutableParameter
from dataclasses import dataclass


if TYPE_CHECKING:
    from ..properties import Properties


T = TypeVar('T', bound=Any)


@dataclass(frozen=True)
class Item(Generic[T]):
    name: str
    value: T


class ChoiceParameter(MutableParameter[int], Generic[T]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        choices: tuple[T | Item[T], ...],
        default_value: CallableValue[int],
        value: CallableValue[int] | _UNSET_TYPE = _UNSET,
        validator: Callable[[int], Any] | _UNSET_TYPE = _UNSET,
    ) -> None:
        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            value=value,
            validator=self._validator_factory(validator),
            converter=int
        )

        self._choices = choices

    @property
    def choices(self) -> tuple[T | Item[T], ...]:
        return self._choices

    def real_value(self) -> T:
        result = self._choices[self.value]
        if isinstance(result, Item):
            return result.value
        return result

    def _validator_factory(
        self,
        validator: Callable[[int], Any] | _UNSET_TYPE
    ) -> Callable[[int], None]:
        def real_validator(value: int) -> None:
            if (len(self._choices) - 1) > value:
                raise ValueError('Index out of range!')
            if not isinstance(validator, _UNSET_TYPE):
                validator(value)
        return real_validator
