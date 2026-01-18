from __future__ import annotations

from typing import TYPE_CHECKING, Any
from asyncio import Lock
from collections.abc import Callable, Iterable, Awaitable

from funpayhub.lib.properties.base import UNSET, _UNSET, Entry


if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties


_NOT_SET = object()


class Parameter[ValueT](Entry):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        value: ValueT,
        flags: Iterable[Any] | None = None,
    ) -> None:
        """
        Базовый класс неизменяемого параметра.

        Значение неизменяемых параметров обычно образуется из значений других параметров,
        параметров запуска приложения и т.д.

        Т.к. параметр неизменяемый, он не может быть сохранен в файл.

        :param id: ID параметра.
        :param name: Название параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param description: Описание параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param value: Значение параметра. Может быть любым объектом или функцией,
            которая не принимает аргументов и возвращает значение параметра.
        """
        super().__init__(id=id, name=name, description=description, flags=flags)
        self._value = value

    @property
    def value(self) -> ValueT:
        """Значение параметра."""
        return self._value

    @property
    def parent(self) -> Properties | None:
        """
        Категория параметров, к которой принадлежит данный параметр.

        Из-за особенности архитектуры параметры **всегда** принадлежат какой-то категории
        (имеют родителя).
        """
        return super().parent  # type: ignore  # always has a parent

    @parent.setter
    def parent(self, value: Properties | None) -> None:
        from ..properties import Properties

        if value and self.parent:
            raise RuntimeError('Already has a parent.')
        if value is not None and not isinstance(value, Properties):
            raise ValueError('Parent of parameter must be an instance of `Properties`.')
        self._parent = value

    @property
    def serialized_value(self) -> Any:
        return self.value


class MutableParameter[ValueT](Parameter[ValueT]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        default_value: ValueT | _NOT_SET = _NOT_SET,
        default_factory: Callable[[], ValueT] | _NOT_SET = _NOT_SET,
        converter: Callable[[Any], ValueT],
        validator: Callable[[ValueT], Awaitable[None]] | _UNSET = UNSET,
        flags: Iterable[Any] | None = None,
    ) -> None:
        """
        Базовый класс изменяемого параметра.

        :param id: ID параметра.
        :param name: Название параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param description: Описание параметра. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param default_value: Значение параметра по умолчанию.  Может быть любым объектом или
            функцией, которая не принимает аргументов и возвращает значение параметра.
        :param converter: Функция-конвертер, которая в качестве единственного аргумента принимает
            любой тип данных и возвращает конвертированный в тип данных параметра объект.
            Если конвертация невозможна, функция должна бросать `ValueError` с текстом ошибки.
            **У каждого параметра обязательно должен быть конвертер.**
        :param validator: Функция-валидатор, которая в качестве единственного аргумента
            принимает уже конвертированный объект и проверяет его валидность.
            Если значение невалидно, должна бросать `ValueError` с текстом ошибки.
        """
        if default_value is _NOT_SET and default_factory is _NOT_SET:
            raise ValueError(
                'Expected exactly one of default_value or default_factory, but neither was provided.',
            )
        if default_value is not _NOT_SET and default_factory is not _NOT_SET:
            raise ValueError(
                'Expected exactly one of default_value or default_factory, but both were provided.',
            )

        self._converter = converter
        self._validator = validator
        self._default_value = default_value
        self._default_factory = default_factory
        self._changing_lock = Lock()

        super().__init__(
            id=id,
            name=name,
            description=description,
            value=self.default_value,
            flags=flags,
        )

    @property
    def default_value(self) -> ValueT:
        if self._default_value is not _NOT_SET:
            return self._default_value
        return self._default_factory()

    async def set_value(
        self,
        value: Any,
        *,
        skip_converter: bool = False,
        skip_validator: bool = False,
        save: bool = True,
    ) -> None:
        """
        Конвертирует, валидирует и устанавливает значение параметра.

        :param value: Новое значение параметра.
        :param skip_converter: Пропустить этап конвертации. Если `True`, значение будет передано
            валидатору в том виде, в котором оно было передано в данный метод.
        :param skip_validator: Пропустить этап валидации. Если `True`, значение будет установлено
            без проверки.
        :param save: Сохранить значение в файл.
        """
        async with self._changing_lock:
            if not skip_converter:
                value = self.convert(value)
            if not skip_validator:
                await self.validate(value)

            self._value = value
            if save:
                await self.save()

    async def next_value(self, save: bool = True) -> ValueT:
        raise NotImplementedError(f'{self.__class__.__name__} does not support `.next_value`.')

    async def to_default(self, save: bool = True) -> None:
        await self.set_value(self.default_value, skip_converter=True, save=save)

    def convert(self, value: Any) -> ValueT:
        """
        Конвертирует объект в нужный параметру тип.

        :param value: Объект, который необходимо конвертировать.
        :return: Конвертированный объект.
        """
        return self._converter(value)

    async def validate(self, value: ValueT) -> None:
        """
        Валидирует переданное значение.

        :param value: Значение, которое необходимо валидировать.
        """
        if not isinstance(self._validator, _UNSET):
            await self._validator(value)

    async def save(self) -> None:
        """
        Сохраняет значение в файл.
        """
        if self.parent is None:
            raise RuntimeError(
                'Cannot save parameter value because it is not attached to any '
                '`Properties` instance.',
            )
        self.parent.save()
