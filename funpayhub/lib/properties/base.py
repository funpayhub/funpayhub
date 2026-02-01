from __future__ import annotations


__all__ = ['Entry']


from typing import Any, Union, TypeVar, Callable
from collections.abc import Iterable, Generator


ParamValueType = TypeVar('ParamValueType')
CallableValue = Union[ParamValueType, Callable[[], ParamValueType]]


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
        flags: Iterable[Any] | None = None,
    ) -> None:
        """
        Базовый класс для параметров / категорий параметров.

        :param parent: Родительский объект.
        :param id: ID объекта.
        :param name: Название объекта. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param description: Описание объекта. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param flags: Флаги объекта.
        """
        if not id:
            raise ValueError('Entry ID cannot be empty.')

        self._parent = parent
        self._id = id
        self._name = name
        self._description = description
        self._flags = frozenset(flags) if flags else frozenset()

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
    def path(self) -> list[str]:
        """
        Путь до объекта начиная с корневого объекта.

        Объединяет ID объектов от родительского до данного в одну строку, разделяя их точкой.
        """
        if self.parent is None:
            return []
        return [*self.parent.path, self.id]

    @property
    def root(self) -> Entry:
        """Корневой объект."""
        return self.parent.root if self.parent is not None else self

    @property
    def is_root(self) -> bool:
        """
        Является ли данный объект корневым?
        (True, если нет родителя, иначе - False)
        """
        return self.parent is None

    @property
    def chain_to_root(self) -> Generator[Entry, None, None]:
        """
        Генератор до корневого объекта.
        """
        yield self
        if self.parent:
            yield from self.parent.chain_to_root

    @property
    def flags(self) -> frozenset[Any]:
        return self._flags

    def has_flag(self, flag: Any) -> bool:
        return flag in self._flags

    def matches_path(self, path: list[str]) -> bool:
        self_path = self.path
        if len(self_path) != len(path):
            return False

        for index, i in enumerate(path):
            if i == '*':
                continue
            if self_path[index] != i:
                return False
        return True
