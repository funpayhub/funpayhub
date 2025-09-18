from __future__ import annotations

from typing import Any, Union, TypeVar, Callable
from collections.abc import Generator


ParamValueType = TypeVar('ParamValueType')
CallableValue = Union[ParamValueType, Callable[[], ParamValueType]]


class _UNSET_TYPE:
    __slots__ = ()

    def __bool__(self) -> bool:
        return False


_UNSET = _UNSET_TYPE()


def resolve(value: CallableValue[ParamValueType]) -> ParamValueType:
    return value() if callable(value) else value


class Entry:
    def __init__(
        self,
        *,
        parent: Entry | None = None,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        flags: set[Any] | None = None,
    ) -> None:
        """
        Базовый класс для параметров / категорий параметров.

        :param parent: родительский объекта.
        :param id: ID объекта.
        :param name: название объекта. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param description: описание объекта. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param flags: флаги объекта.
        """
        if '.' in id or id.isnumeric():
            raise ValueError("Entry id must not contain '.' and must not be a number.")
        self._parent = parent
        self._id = id
        self._name = name
        self._description = description
        self._flags = flags or set()

    @property
    def id(self) -> str:
        """ID объекта."""
        return self._id

    @property
    def name(self) -> str:
        """Имя объекта."""
        return resolve(self._name)

    @property
    def description(self) -> str:
        """Описание объекта."""
        return resolve(self._description)

    @property
    def parent(self) -> Entry | None:
        """Родительский объект."""
        return self._parent

    @property
    def path(self) -> str:
        """
        Путь до объекта начиная с корневого объекта.

        Объединяет ID объектов от родительского до данного в одну строку, разделяя их точкой.
        """
        if self._parent is None:
            return ''
        return self._parent.path + (f'.{self.id}' if self._parent.path else self.id)

    @property
    def root(self) -> Entry:
        """Корневой объект."""
        if self.parent is None:
            return self
        return self.parent.root

    @property
    def is_root(self) -> bool:
        """
        Является ли данный объект корневым?
        (True, если нет родителя, иначе - False)
        """
        return self.parent is not None

    @property
    def chain_to_root(self) -> Generator[Entry, None, None]:
        """
        Генератор до корневого объекта.
        """
        yield self
        if self.parent:
            yield from self.parent.chain_to_root
