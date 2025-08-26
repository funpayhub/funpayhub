from __future__ import annotations

from typing import Any, Union, TypeVar, Callable
from collections.abc import Generator


ParamValueType = TypeVar('ParamValueType', bound=Any)
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
    ) -> None:
        if '.' in id or id.isnumeric():
            raise ValueError('Entry id must not contain \'.\' and must not be a number.')
        self._parent = parent
        self._id = id
        self._name = name
        self._description = description

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return resolve(self._name)

    @property
    def description(self) -> str:
        return resolve(self._description)

    @property
    def parent(self) -> Entry | None:
        return self._parent

    @property
    def path(self) -> str:
        if self._parent is None:
            return ''
        return self._parent.path + (f'.{self.id}' if self._parent.path else self.id)

    @property
    def root(self) -> Entry:
        if self.parent is None:
            return self
        return self.parent.root

    @property
    def chain_to_root(self) -> Generator[Entry, None, None]:
        yield self
        if self.parent:
            yield from self.parent.chain_to_root
