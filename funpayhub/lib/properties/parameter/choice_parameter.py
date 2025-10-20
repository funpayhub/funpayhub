from __future__ import annotations


__all__ = ['ChoiceParameter', 'Choice']


from typing import TYPE_CHECKING, Any
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Callable, Iterable, Awaitable

from funpayhub.lib.properties.base import UNSET, _UNSET
from funpayhub.lib.properties.parameter.base import MutableParameter
from funpayhub.lib.properties.parameter.converters import string_converter


if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class Choice[T: int | float | bool | str]:
    id: str
    name: str
    value: T

    def __post_init__(self) -> None:
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
        choices: tuple[Choice[T], ...],
        default_value: str,
        validator: Callable[[str], Awaitable[None]] | _UNSET = UNSET,
        flags: Iterable[Any] | None = None,
    ) -> None:
        if not choices:
            raise ValueError('choices cannot be empty')  # todo

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
            validator=validator,
            converter=string_converter,
            flags=flags,
        )

    def add_choice(self, choice: Choice[T]) -> None:
        if not isinstance(choice, Choice):
            raise ValueError('Choice must be an instance of `Choice`.')
        if choice.id in self._choices:
            raise ValueError('Choice already defined.')
        self._choices[choice.id] = choice

    @property
    def choices(self) -> MappingProxyType[str, Choice[T]]:
        return MappingProxyType(self._choices)

    @property
    def real_value(self) -> T:
        return self.choices[self.value].value

    async def validate_value(self, value: str) -> None:
        if value not in self._choices:
            raise ValueError(f'No choice with id {value!r}.')
        await super().validate(value)

    def __len__(self) -> int:
        return len(self.choices)
