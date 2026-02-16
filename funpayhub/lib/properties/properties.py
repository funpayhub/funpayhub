from __future__ import annotations

from funpayhub.lib.translater import _en


__all__ = ['Properties']


import os
import tomllib
from typing import Any, Literal
from types import EllipsisType, MappingProxyType
from collections.abc import Callable, Iterable, Awaitable, Generator

import tomli_w

from funpayhub.loggers import main as logger

from .base import Node
from .parameter.base import Parameter, MutableParameter


class Properties(Node):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        file: str | None = None,
        flags: Iterable[Any] | None = None,
        on_parameter_changed_hook: Callable[[MutableParameter], Awaitable[None]]
        | EllipsisType = ...,
        on_node_attached_hook: Callable[[Node], Awaitable[None]] | EllipsisType = ...,
        on_node_detached_hook: Callable[[Node], Awaitable[None]] | EllipsisType = ...,
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
        :param file: Путь к файлу для сохранения категории. Если `None` —
            используется файл родительской категории.
        """
        self._file = file
        self._nodes: dict[str, Node] = {}

        self._on_node_attached_hook = on_node_attached_hook
        self._on_node_detached_hook = on_node_detached_hook
        self._on_parameter_changed_hook = on_parameter_changed_hook

        super().__init__(
            id=id,
            name=name,
            description=description,
            flags=flags,
        )

    @property
    def chain_to_tail(self) -> Generator[Properties, None, None]:
        """
        Генератор всех категорий от текущей до всех листовых узлов.

        :yield: Текущая категория и все вложенные конечные категории (без дочерних элементов).
        """
        yield self
        for entry in self._nodes.values():
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
    ) -> MappingProxyType[str, Node]:
        """
        Неизменяемый словарь со всеми вложенными элементами (параметрами / подкатегориями).
        """
        return MappingProxyType(self._nodes)

    def attach_node[T: Node](self, node: T, replace: bool = False) -> T:
        if node.id in self._nodes:
            if not replace:
                raise ValueError(f'Node with ID {node.id!r} already exists.')
            self.detach_node(node.id)

        node.parent = self
        self._nodes[node.id] = node
        return node

    def detach_node(self, node_id: str) -> Properties | None:
        node = self._nodes.get(node_id)
        if not isinstance(node, Properties):
            return None

        self._nodes.pop(node_id)
        node.parent = None
        return node

    def as_dict(
        self,
        same_file_only: bool = True,
        exclude_immutable_parameters: bool = True,
    ) -> dict[str, Any]:
        total: dict[str, Any] = {}
        for v in self._nodes.values():
            if isinstance(v, Parameter):
                if not isinstance(v, MutableParameter) and exclude_immutable_parameters:
                    continue
                total[v.id] = v.serialized_value
            elif isinstance(v, Properties):
                if same_file_only and self.file_to_save != v.file_to_save:
                    continue
                total[v.id] = v.as_dict()
        return total

    async def save(
        self,
        same_file_only: bool = False,
    ) -> None:
        if not self._file:
            if self.parent is None:
                raise RuntimeError(f'Unable to save properties {self.id!r}: parent is None.')
            await self.parent.save(same_file_only=same_file_only)
            return

        if not os.path.exists(self._file):
            os.makedirs(os.path.dirname(self._file), exist_ok=True)

        total = self.as_dict()
        with open(self._file, 'w', encoding='utf-8') as f:
            f.write(tomli_w.dumps(total, multiline_strings=True))

        if not same_file_only:
            for props in self.chain_to_tail:
                if props._file and props.file_to_save != self.file_to_save:
                    await props.save()
                    # todo: один и тот же файл сохраняется несколько раз,
                    #  если в подузлах есть узлы с таким же файлом.

    async def load(self) -> None:
        data = {}
        if self.file and os.path.exists(self.file):
            with open(self.file, 'r', encoding='utf-8') as f:
                data = tomllib.loads(f.read())
        await self.load_from_dict(data)

    async def load_from_dict(self, properties_dict: dict[str, Any]) -> None:
        await self._set_values(properties_dict)

    async def _set_values(self, values: dict[str, Any]) -> None:
        for v in self._nodes.values():
            if isinstance(v, Properties):
                await v.load() if v.file else await v.load_from_dict(values[v.id])
            elif v.id not in values:
                continue
            elif isinstance(v, MutableParameter):
                await v.set_value(values[v.id], save=False)

    def get_node(
        self,
        path: list[str | int],
    ) -> Properties | Parameter[Any] | MutableParameter[Any]:
        if not path:
            return self

        segment = path[0]
        if isinstance(segment, str):
            next_entry = self.entries.get(segment)
            if next_entry is None:
                raise LookupError(f'{self.path!r} has no entry with id {segment!r}.')
        elif isinstance(segment, int):
            try:
                key = list(self.entries.keys())[segment]
            except:
                raise LookupError(f'{self.path!r} has no entry at index {segment}.')
            next_entry = self.entries[key]
        else:
            raise ValueError(
                f"Segment of path must be an instance of 'str' or 'int', "
                f'not {segment.__class__.__name__!r}',
            )

        if isinstance(next_entry, Parameter):
            if len(path) > 1:
                raise LookupError(f'No entry with path {path!r}.')
            return next_entry

        if isinstance(next_entry, Properties):
            if len(path) > 1:
                return next_entry.get_node(path[1:])
            return next_entry

        raise LookupError(f'No entry with path {path!r}.')

    def get_parameter(self, path: list[str | int]) -> Parameter[Any] | MutableParameter[Any]:
        result = self.get_node(path)
        if not isinstance(result, Parameter):
            raise LookupError(f'No parameter with path {path}')
        return result

    def get_properties(self, path: list[str | int]) -> Properties:
        result = self.get_node(path)
        if not isinstance(result, Properties):
            raise LookupError(f'No properties with path {path}')
        return result

    async def _execute_hook(
        self,
        hook: Literal['on_attach', 'on_detach', 'on_change'],
        trigger: Node,
    ) -> None:
        if not self.is_root:
            return await self.parent._execute_hook(hook, trigger)

        hooks = {
            'attach': self._on_node_attached_hook,
            'detach': self._on_node_detached_hook,
            'change': self._on_parameter_changed_hook,
        }
        hook_callable = hooks.get(hook)

        if hook_callable in [None, Ellipsis]:
            return None

        try:
            await hook_callable(trigger)
        except Exception:
            logger.error(
                _en('An error occurred while executing %s trigger for %s'),
                hook,
                '.'.join(trigger.path),
                exc_info=True,
            )

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, item: str) -> Node:
        return self._nodes[item]

    def __contains__(self, item: str) -> bool:
        return item in self._nodes
