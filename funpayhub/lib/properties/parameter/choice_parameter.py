from __future__ import annotations


__all__ = ['ChoiceParameter', 'Choice']


from typing import TYPE_CHECKING, Any, Union, Generic, TypeVar
from dataclasses import dataclass
from collections.abc import Callable

from funpayhub.lib.properties.base import UNSET, _UNSET
from funpayhub.lib.properties.parameter.base import MutableParameter
from funpayhub.lib.properties.parameter.converters import int_converter


if TYPE_CHECKING:
    from ..properties import Properties


@dataclass(frozen=True)
class Choice[T: int | float | bool | str]:
    id: str
    name: str
    value: T

    def __post_init__(self):
        if not self.id:
            raise ValueError('Choice ID cannot be empty.')
        if not isinstance(self.value, int | float | bool | str):
            raise ValueError('Choice value must be of type int, float, bool or str.')


class ChoiceParameter[T: int | float | bool | str](MutableParameter[str]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        choices: tuple[Choice[T]],
        default_value: str,
        validator: Callable[[int], Any] | _UNSET = UNSET,
        flags: set[Any] | None = None,
    ) -> None:
        if not choices:
            raise ValueError("choices cannot be empty")  # todo

        self._serialized_choices: dict[str, Any] = {}
        self._choices: dict[str, Choice[Any]] = {}

        for i in choices:
            self.add_choice(i)

        if default_value not in self._choices:
            raise ValueError(f'`default_value` must be one of: {", ".join(self._choices.keys())}')


        super().__init__(
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            validator=self._validator_factory(validator),
            converter=int_converter,
            flags=flags
        )

    def add_choice(self, choice: Choice[T]) -> None:
        if not isinstance(choice, Choice):
            raise ValueError('Choice must be an instance of `Choice`.')
        if choice.id in self._choices:
            raise ValueError('Choice already defined.')
        self._choices[choice.id] = choice

    def delete_choice(self, choice: str) -> None:
        if choice == self.default_value:
            raise ValueError('Default choice cannot be deleted.')
        if self.value == choice:
            self.set_value(self.default_value, skip_converter=True)
        self._choices.pop(choice, None)


    @property
    def choices(self) -> tuple[Union[T, Item[T]], ...]:
        return self._choices

    def real_value(self) -> T:
        result = self.choices[self.value]
        if isinstance(result, Item):
            return result.value
        return result

    def _validator_factory(
        self,
        validator: Callable[[int], Any] | _UNSET,
    ) -> Callable[[int], None]:
        def real_validator(value: int) -> None:
            if value > len(self.choices) - 1:
                raise ValueError('Index out of range!')  # todo: validation text
            if not isinstance(validator, _UNSET):
                validator(value)

        return real_validator

    def __len__(self) -> int:
        return len(self.choices)
