from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union, Generic, TypeVar
from abc import ABC
from collections.abc import Callable

from typing_extensions import Self

from funpayhub.lib.properties.base import _UNSET, _UNSET_TYPE, Entry


if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties


ValueT = TypeVar('ValueT')
PropertiesT = TypeVar('PropertiesT', bound='Properties', default='Properties')

CallableValue = Union[ValueT, Callable[[], ValueT]]


def resolve(value: CallableValue[ValueT]) -> ValueT:
    return value() if callable(value) else value


class Parameter(Entry, Generic[ValueT, PropertiesT]):
    def __init__(
        self,
        *,
        properties: PropertiesT,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        value: CallableValue[ValueT],
        flags: set[Any] | None = None
    ) -> None:
        """
        Базовый класс неизменяемого параметра.

        Значение неизменяемых параметров обычно образуется из значений других параметров,
        параметров запуска приложения и т.д.

        Т.к. параметр неизменяемый, он не может быть сохранен в файл.

        :param properties: объект категории параметров, к которому принадлежит данный параметр.
            (родительский объект).
        :param id: ID параметра.
        :param name: Название параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param description: Описание параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param value: Значение параметра. Может быть любым объектом или функцией,
            которая не принимает аргументов и возвращает значение параметра.
        """
        super().__init__(id=id, name=name, description=description, parent=properties, flags=flags)
        self._value = value

    @property
    def value(self) -> ValueT:
        """Значение параметра."""
        return resolve(self._value)

    @property
    def parent(self) -> PropertiesT:
        """
        Категория параметров, к которой принадлежит данный параметр.

        Из-за особенности архитектуры параметры **всегда** принадлежат какой-то категории
        (имеют родителя).
        """
        return super().parent  # type: ignore  # always has a parent

    @property
    def serialized_value(self) -> Any:
        return self.value


class MutableParameter(Parameter[ValueT, PropertiesT]):
    def __init__(
        self,
        *,
        properties: PropertiesT,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        default_value: CallableValue[ValueT],
        value: CallableValue[ValueT] | _UNSET_TYPE = _UNSET,
        validator: Callable[[ValueT], Any] | _UNSET_TYPE = _UNSET,
        converter: Callable[[Any], ValueT],
        flags: set[Any] | None = None,
    ) -> None:
        """
        Базовый класс изменяемого параметра.

        :param properties: Объект категории параметров, к которому принадлежит данный параметр.
            (родительский объект).
        :param id: ID параметра.
        :param name: Название параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param description: Описание параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param default_value: Значение параметра по умолчанию.  Может быть любым объектом или
            функцией, которая не принимает аргументов и возвращает значение параметра.
        :param value: Значение параметра. Может быть любым объектом или функцией,
            которая не принимает аргументов и возвращает значение параметра.
        :param converter: Функция-конвертер, которая в качестве единственного аргумента принимает
            любой тип данных и возвращает конвертированный в тип данных параметра объект.
            Если конвертация невозможна, функция должна бросать `ValueError` с текстом ошибки.
            **У каждого параметра обязательно должен быть конвертер.**
        :param validator: Функция-валидатор, которая в качестве единственного аргумента
            принимает уже конвертированный объект и проверяет его валидность.
            Если значение невалидно, должна бросать `ValueError` с текстом ошибки.
        """
        self._convertor = converter
        self._validator = validator

        # self.validate(default_value)
        self._default_value = default_value

        if not isinstance(value, _UNSET_TYPE):
            value = self.convert(value)
            # self.validate(value)

        super().__init__(
            properties=properties,
            id=id,
            name=name,
            description=description,
            value=value if not isinstance(value, _UNSET_TYPE) else default_value,
            flags=flags
        )

    @property
    def default_value(self) -> ValueT:
        """Значение параметра по умолчанию."""
        return resolve(self._default_value)

    def set_value(
        self,
        value: Any,
        *,
        skip_converter: bool = False,
        skip_validator: bool = False,
        save: bool = True,
    ) -> Self:
        """
        Конвертирует, валидирует и устанавливает значение параметра.

        :param value: Новое значение параметра.
        :param skip_converter: Пропустить этап конвертации. Если `True`, значение будет передано
            валидатору в том виде, в котором оно было передано в данный метод.
        :param skip_validator: Пропустить этап валидации. Если `True`, значение будет установлено
            без проверки.
        :param save: Сохранить значение в файл.
        """
        if not skip_converter:
            value = self.convert(value)
        if not skip_validator:
            self.validate(value)

        self._value = value
        if save:
            self.save()
        return self

    def convert(self, value: Any) -> ValueT:
        """
        Конвертирует объект в нужный параметру тип.

        :param value: Объект, который необходимо конвертировать.
        :return: Конвертированный объект.
        """
        return self._convertor(value)

    def validate(self, value: Any) -> None:
        """
        Валидирует переданное значение.

        :param value: Значение, которое необходимо валидировать.
        """
        if not isinstance(self._validator, _UNSET_TYPE):
            self._validator(value)

    def save(self) -> None:
        """
        Сохраняет значение в файл.
        """
        self.parent.save()
        # У параметров родитель - всегда категория параметров.
