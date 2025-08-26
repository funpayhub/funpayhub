from __future__ import annotations

__all__ = ['Properties',]


import os
import tomllib
from typing import Any, TypeVar
from collections.abc import Generator

import tomli_w

from .base import Entry, CallableValue
from .parameter.base import Parameter, MutableParameter
from types import MappingProxyType


T = TypeVar('T', bound='Parameter[Any]')
P = TypeVar('P', bound='Properties')


class Properties(Entry):
    def __init__(
        self,
        *,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        parent: Properties | None = None,
        file: str | None = None,
    ) -> None:
        if parent is not None and not isinstance(parent, Properties):
            raise TypeError('Parent should be an instance of Properties.')

        self._file = file
        self._entries: dict[str, Parameter[Any] | MutableParameter[Any] | Properties] = {}

        super().__init__(
            parent=parent,
            id=id,
            name=name,
            description=description
        )

    @property
    def parent(self) -> Properties | None:
        return super().parent  # type: ignore  # check in __init__

    @parent.setter
    def parent(self, value: Properties) -> None:
        if self._parent is not None:
            raise RuntimeError('Already has a parent')
        self._parent = value

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def root(self) -> Properties:
        return super().root  # type: ignore  # check in __init__

    @property
    def chain_to_root(self) -> Generator[Properties, None, None]:
        return super().chain_to_root  # type: ignore  # check in __init__

    @property
    def chain_to_tail(self) -> Generator[Properties, None, None]:
        yield self
        for entry in self._entries.values():
            if isinstance(entry, Properties):
                yield from entry.chain_to_tail

    @property
    def file(self) -> str | None:
        return self._file

    @property
    def file_to_save(self) -> str | None:
        return self.file or (self.parent.file_to_save if self.parent else None)

    @property
    def entries(self) -> MappingProxyType[str, Parameter[Any] | MutableParameter[Any] | Properties]:
        return MappingProxyType(self._entries)

    def attach_parameter(self, param: T) -> T:
        if param.id in self._entries:
            raise RuntimeError('ID already exists')
        self._entries[param.id] = param
        return param

    def unattach_parameter(self, id: str) -> Parameter[Any] | None:
        result = self._entries.get(id)
        if result is not None and not isinstance(result, Parameter):
            raise ValueError(f'{id} is not a Parameter, but {result.__class__.__name__}.')
        self._entries.pop(id, None)
        return result

    def attach_properties(self, properties: P) -> P:
        if properties.id in self._entries:
            raise RuntimeError('ID already exists')
        properties.parent = self
        self._entries[properties.id] = properties
        return properties

    def unattach_properties(self, id: str) -> Properties | None:
        result = self._entries.get(id)
        if result is not None and not isinstance(result, Properties):
            raise ValueError(f'{id} is not a Properties, but {result.__class__.__name__}.')
        self._entries.pop(id, None)
        return result

    def as_dict(
        self,
        same_file_only: bool = True,
        exclude_immutable_parameters: bool = True,
    ) -> dict[str, Any]:
        total: dict[str, Any] = {}
        for v in self._entries.values():
            if isinstance(v, Parameter):
                if not isinstance(v, MutableParameter) and exclude_immutable_parameters:
                    continue
                total[v.id] = v.value
            elif isinstance(v, Properties):
                if same_file_only and self.file_to_save != v.file_to_save:
                    continue
                total[v.id] = v.as_dict()
        return total

    def save(
        self,
        same_file_only: bool = False,
    ) -> None:
        if not self._file:
            if not self.parent:
                raise RuntimeError('Unable to save')
            return self.parent.save(same_file_only=True)

        if not os.path.exists(self._file):
            os.makedirs(os.path.dirname(self._file), exist_ok=True)

        total = self.as_dict()
        with open(self._file, 'w', encoding='utf-8') as f:
            f.write(tomli_w.dumps(total, multiline_strings=True))

        if not same_file_only:
            for props in self.chain_to_tail:
                if props._file and props.file_to_save != self.file_to_save:
                    props.save()  # todo

    def load(self) -> None:
        data = {}
        if self.file and os.path.exists(self.file):
            with open(self.file, 'r', encoding='utf-8') as f:
                data = tomllib.loads(f.read())

        self._set_values(data)

    def _set_values(self, values: dict[str, Any]) -> None:
        for v in self._entries.values():
            if isinstance(v, Properties) and v.file:
                v.load()
            elif v.id not in values:
                continue
            elif isinstance(v, MutableParameter):
                v.set_value(values[v.id], save=False)
            elif isinstance(v, Properties):
                v._set_values(values[v.id])

    def get_entry(self, path: str) -> Entry:
        if not path:
            return self

        split = path.split('.')
        next_entry = self.entries.get(split[0])
        if isinstance(next_entry, Parameter):
            return next_entry
        elif isinstance(next_entry, Properties):
            try:
                return next_entry.get_entry('.'.join(split[1:]))
            except LookupError as e:
                raise LookupError(f'No entry with path {path}') from e
        else:
            raise LookupError(f'No entry with path {path}') from None

    def get_parameter(self, path: str) -> Parameter[Any] | MutableParameter[Any]:
        result = self.get_entry(path)
        if not isinstance(result, Parameter):
            raise LookupError(f'No parameter with path {path}')
        return result

    def get_properties(self, path: str) -> Properties:
        result = self.get_entry(path)
        if not isinstance(result, Properties):
            raise LookupError(f'No properties with path {path}')
        return result