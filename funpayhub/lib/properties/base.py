from __future__ import annotations


__all__ = ['Node']


import logging
from typing import TYPE_CHECKING, Any, Union, TypeVar, Callable
from collections.abc import Iterable, Generator


if TYPE_CHECKING:
    from .properties import Properties


ParamValueType = TypeVar('ParamValueType')
CallableValue = Union[ParamValueType, Callable[[], ParamValueType]]


logger = logging.getLogger('properties')


def resolve(value: CallableValue[ParamValueType]) -> ParamValueType:
    return value() if callable(value) else value


class Node:
    def __init__(
        self,
        *,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        flags: Iterable[Any] | None = None,
        hooks: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        """
        Базовый класс для параметров / категорий параметров.

        :param id: ID объекта.
        :param name: Название объекта. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param description: Описание объекта. Может быть строкой или функцией,
            которая не принимает аргументов и возвращает строку.
        :param flags: Флаги объекта.
        """
        if not id:
            raise ValueError('Node ID cannot be empty.')

        self._parent = None
        self._id = id
        self._name = name
        self._description = description
        self._flags = frozenset(flags) if flags else frozenset()

        self.__hooks__ = hooks or {}

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
    def parent(self) -> Properties | None:
        """Родительский объект."""
        return self._parent

    @parent.setter
    def parent(self, value: Properties | None) -> None:
        if value is None:
            self._parent = None
            return

        from .properties import Properties

        if self.parent is not None:
            raise RuntimeError(f'Node {self.id!r} already has a parent {self.parent.id!r}.')
        if not isinstance(value, Properties):
            raise ValueError('Parent of Node must be an instance of `Properties`.')
        self._parent = value

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
    def root(self) -> Node:
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
    def chain_to_root(self) -> Generator[Node, None, None]:
        """
        Генератор до корневого объекта.
        """
        yield self
        if self.parent:
            yield from self.parent.chain_to_root

    @property
    def flags(self) -> frozenset[Any]:
        return self._flags

    def is_child(self, path_or_node: list[str] | Node) -> bool:
        path = path_or_node if isinstance(path_or_node, list) else path_or_node.path
        if path == self.path:
            return False

        if len(self.path) <= len(path):
            return False

        return path == self.path[: len(path)]

    def has_flag(self, flag: Any) -> bool:
        return flag in self._flags

    def get_flag[R](self, flag_type: type[R]) -> R | None:
        for i in self.flags:
            if isinstance(i, flag_type):
                return i
        return None

    async def emit(self, hook: str, *args: Any, **kwargs: Any) -> None:
        if (hook_obj := self.__hooks__.get(hook)) is not None:
            try:
                await hook_obj(*args, **kwargs)
            except Exception:
                logger.error(
                    'An error occured while running hook %s in node %s.',
                    hook,
                    self.path,
                    exc_info=True,
                )

        if self.parent is not None:
            await self.parent.emit(hook, *args, **kwargs)
