from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union, Generic, TypeVar
from abc import ABC
from collections.abc import Callable

from typing_extensions import Self

from funpayhub.lib.properties.base import _UNSET, _UNSET_TYPE, Entry


if TYPE_CHECKING:
    from ..properties import Properties


ParamValueType = TypeVar('ParamValueType')
CallableValue = Union[ParamValueType, Callable[[], ParamValueType]]


def resolve(value: CallableValue[ParamValueType]) -> ParamValueType:
    return value() if callable(value) else value


class Parameter(Entry, ABC, Generic[ParamValueType]):
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        value: CallableValue[ParamValueType],
    ) -> None:
        """
        Базовый класс неизменяемого параметра.

        Значение неизменяемых параметров обычно образуется из значений других параметров,
        параметров запуска приложения и т.д.

        Т.к. параметр неизменяемый, он не может быть сохранен в файл.

        :param properties: объект категории параметров, к которому принадлежит данный параметр.
            (родительский объект).

        :param id: ID параметра.
        :param name: название параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param description: описание параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param value: значение параметра. Может быть любым объектом или функцией,
            которая не принимает аргументов и возвращает значение параметра.
        """
        super().__init__(id=id, name=name, description=description, parent=properties)
        self._value = value

    @property
    def value(self) -> ParamValueType:
        """Значение параметра."""
        return resolve(self._value)

    @property
    def parent(self) -> Properties:
        """
        Категория параметров, к которой принадлежит данный параметр.

        Из-за особенности архитектуры параметры **всегда** принадлежат какой-то категории
        (имеют родителя).
        """
        return super().parent  # type: ignore  # always has a parent

    @property
    def properties(self) -> Properties:
        return self.parent

    @property
    def serialized_value(self) -> Any:
        return self.value


class MutableParameter(Parameter[ParamValueType]):
    """
    Класс изменяемого параметра.
    """
    def __init__(
        self,
        *,
        properties: Properties,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        default_value: CallableValue[ParamValueType],
        value: CallableValue[ParamValueType] | _UNSET_TYPE = _UNSET,
        validator: Callable[[ParamValueType], Any] | _UNSET_TYPE = _UNSET,
        converter: Callable[[str], ParamValueType],
    ) -> None:
        self._convertor = converter
        self._validator = validator

        self.validate(default_value)
        self._default_value = default_value

        if not isinstance(value, _UNSET_TYPE):
            value = self.convert(value)
            self.validate(value)

        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            value=value if not isinstance(value, _UNSET_TYPE) else default_value,
        )

    @property
    def default_value(self) -> ParamValueType:
        return resolve(self._default_value)

    def set_value(
        self,
        value: ParamValueType | str,
        *,
        skip_converter: bool = False,
        skip_validator: bool = False,
        save: bool = True,
    ) -> Self:
        if not skip_converter:
            value = self.convert(value)
        if not skip_validator:
            self.validate(value)

        self._value = value
        if save:
            self.save()
        return self

    def convert(self, value: Any) -> ParamValueType:
        return self._convertor(value)

    def validate(self, value: Any) -> None:
        if not isinstance(self._validator, _UNSET_TYPE):
            self._validator(value)

    def save(self) -> None:
        self.parent.save()
