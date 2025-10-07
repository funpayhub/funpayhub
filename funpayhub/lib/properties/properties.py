from __future__ import annotations


__all__ = ['Properties']


import os
import tomllib
from typing import Any, TypeVar, TypeAlias
from types import MappingProxyType
from collections.abc import Generator

import tomli_w
from typing_extensions import Self

from .base import Entry, CallableValue
from .parameter.base import Parameter, MutableParameter


T = TypeVar('T', bound='Parameter[Any, Any]')
InnerEntries: TypeAlias = Parameter[Any] | MutableParameter[Any] | 'Properties'


class Properties(Entry):
    _parent: Properties | None = None

    def __init__(
        self,
        *,
        id: str,
        name: CallableValue[str],
        description: CallableValue[str],
        parent: Properties | None = None,
        file: str | None = None,
        flags: set[Any] | None = None,
    ) -> None:
        """
        Категория параметров.

        Категории могут образовывать иерархию: каждая категория может содержать
        дочерние элементы (параметры или подкатегории) и ссылку на родителя.
        Также поддерживается сохранение в отдельный файл или в файл родительской категории.

        :param id: Уникальный идентификатор категории.
        :param name: Название категории. Может быть строкой или функцией без аргументов,
            возвращающей строку.
        :param description: Описание категории. Может быть строкой или функцией без аргументов,
            возвращающей строку.
        :param parent: Родительская категория. Если `None`, категория является корневой.
        :param file: Путь к файлу для сохранения категории. Если `None` —
            используется файл родительской категории.
        """
        if parent is not None:
            self.parent = parent
        self._file = file
        self._entries: dict[str, InnerEntries] = {}

        super().__init__(
            parent=parent,
            id=id,
            name=name,
            description=description,
            flags=flags,
        )

    @property
    def parent(self) -> Properties | None:
        """Родительская категория или `None`, если категория корневая."""
        return self._parent

    @parent.setter
    def parent(self, value: Properties) -> None:
        if not isinstance(value, Properties):
            raise TypeError('Parent should be an instance of Properties.')
        if self.parent is not None:
            raise ValueError('Already has a parent')
        if value is self:
            raise ValueError('Cannot attach properties to itself.')
        # todo: better checks
        self._parent = value

    @property
    def root(self) -> Properties:
        """Корневая категория (верхний элемент в иерархии)."""
        return super().root  # type: ignore  # check in __init__

    @property
    def chain_to_root(self) -> Generator[Properties, None, None]:
        """
        Генератор всех категорий от текущей до корневой.

        :yield: Категории начиная с текущей и заканчивая корневой.
        """
        return super().chain_to_root  # type: ignore  # check in __init__

    @property
    def chain_to_tail(self) -> Generator[Properties, None, None]:
        """
        Генератор всех категорий от текущей до всех листовых узлов.

        :yield: Текущая категория и все вложенные конечные категории (без дочерних элементов).
        """
        yield self
        for entry in self._entries.values():
            if isinstance(entry, Properties):
                yield from entry.chain_to_tail

    @property
    def file(self) -> str | None:
        """Файл сохранения текущей категории или `None`."""
        return self._file

    @property
    def file_to_save(self) -> str | None:
        """
        Итоговый путь файла для сохранения.

        Если у текущей категории `.file` равен `None`, ищется ближайший родитель с
        ненулевым `.file`. Если такого нет, возвращается `None`.
        """
        return self.file or (self.parent.file_to_save if self.parent else None)

    @property
    def entries(
        self,
    ) -> MappingProxyType[str, Parameter[Any, Self] | MutableParameter[Any, Self] | Properties]:
        """
        Неизменяемый словарь со всеми вложенными элементами (параметрами / подкатегориями).
        """
        return MappingProxyType(self._entries)

    def attach_parameter(self, param: T) -> T:
        if not isinstance(param, Parameter):
            raise ValueError('Parameter should be an instance of Parameter.')
        if param.id in self._entries:
            raise RuntimeError(f'Entry with ID {param.id!r} already exists.')
        self._entries[param.id] = param
        return param

    def attach_properties[P: Properties](self, properties: P) -> P:
        if not isinstance(properties, Properties):
            raise ValueError('Properties should be an instance of Properties.')
        if properties.id in self._entries:
            raise RuntimeError(f'Entry with ID {properties.id!r} already exists.')
        properties.parent = self
        self._entries[properties.id] = properties
        return properties

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
                total[v.id] = v.serialized_value
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
            self.parent.save(same_file_only=True)
            return

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
                v.set_value(values[v.id], save=False, skip_validator=True)
            elif isinstance(v, Properties):
                v._set_values(values[v.id])

    def get_entry(self, path: list[str | int]) -> InnerEntries:
        if not path:
            return self

        segment = path[0]
        if isinstance(segment, int):
            try:
                key = list(self.entries.keys())[segment]
            except:
                raise LookupError(f'{self.path!r} has no entry at index {segment}.')
            next_entry = self.entries[key]
        else:
            next_entry = self.entries.get(segment)
            if next_entry is None:
                raise LookupError(f"{self.path!r} has no entry with id {segment!r}.")

        if isinstance(next_entry, Parameter):
            if len(path) > 1:
                raise LookupError(f"No entry with path {path!r}.")
            return next_entry

        if isinstance(next_entry, Properties):
            if len(path) > 1:
                return next_entry.get_entry(path[1:])
            return next_entry

        raise LookupError(f"No entry with path {path!r}.")

    def get_parameter(self, path: list[str | int]) -> Parameter[Any, Self] | MutableParameter[Any, Self]:
        result = self.get_entry(path)
        if not isinstance(result, Parameter):
            raise LookupError(f'No parameter with path {path}')
        return result

    def get_properties(self, path: list[str | int]) -> Properties:
        result = self.get_entry(path)
        if not isinstance(result, Properties):
            raise LookupError(f'No properties with path {path}')
        return result

    def __len__(self) -> int:
        return len(self.entries)
