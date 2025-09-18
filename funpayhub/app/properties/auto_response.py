from __future__ import annotations
from funpayhub.lib.properties import Properties
from funpayhub.lib.properties.base import Entry
from funpayhub.lib.properties.parameter import StringParameter, ListParameter, ToggleParameter
from types import MappingProxyType
from typing import Any, NoReturn
import tomllib
import os


class AutoResponseEntryProperties(Properties):
    def __init__(self, command: str) -> None:
        super().__init__(
            id=command,
            name=command,
            description=f'$props.auto_response.*',
        )

        self.is_regexp = self.attach_parameter(
            ToggleParameter(
                properties=self,
                id='is_regexp',
                name='$props.auto_response.*.is_regexp:name',
                description='$props.auto_response.*.response_text:description',
                default_value=False
            )
        )

        self.response_text = self.attach_parameter(
            StringParameter(
                properties=self,
                id='response_text',
                name='$props.auto_response.*.response_text:name',
                description='$props.auto_response.*.response_text:description',
                default_value='Ответ на $message_text'
            )
        )

        self.hooks = self.attach_parameter(
            ListParameter(
                properties=self,
                id='hooks',
                name='$props.auto_response.*.hooks:name',
                description='$props.auto_response.*.hooks:description',
                default_value=[]
            )
        )

    @property
    def parent(self) -> AutoResponseEntryProperties | None:
        return super().parent  # type: ignore

    @parent.setter
    def parent(self, value: AutoResponseProperties) -> None:
        if not isinstance(value, AutoResponseProperties):
            raise RuntimeError
        Properties.parent.fset(self, value)

    @property
    def path(self) -> str:
        if not self.parent:
            return ''

        id = self.parent.get_index_by_id(self.id)
        return self.parent.path + (f'.{id}' if self.parent.path else str(id))


class AutoResponseProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='auto_response',
            name='$props.auto_response:name',
            description='$props.auto_response:description',
            file='config/auto_response.toml',
        )

    @property
    def entries(self) -> MappingProxyType[str, AutoResponseEntryProperties]:
        return super().entries  # type: ignore

    def attach_parameter(self, parameter: Any) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support parameters.')

    def detach_parameter(self, id: str) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def attach_properties(self, properties: Any) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def detach_properties(self, id: str) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def load(self):
        if not os.path.exists(self.file):  #type: ignore #  always has file
            return
        with open(self.file, 'r', encoding='utf-8') as f:  #type: ignore #  always has file
            data = tomllib.loads(f.read())

        self._entries = {}
        for i in data:
            obj = AutoResponseEntryProperties(command=i)
            obj._set_values(data[i])
            super().attach_properties(obj)

    def add_entry(self, command: str) -> AutoResponseEntryProperties:
        obj = AutoResponseEntryProperties(command)
        super().attach_properties(obj)
        return obj

    def get_entry(self, path: str) -> Entry:
        if not path:
            return self

        split = path.split('.')
        next_entry = split[0]

        if not next_entry.isnumeric():
            return super().get_entry(path)

        index = int(next_entry)
        try:
            return self.entries[list(self.entries.keys())[index]].get_entry('.'.join(split[1:]))
        except IndexError:
            raise LookupError(f'No entry with name {path}')

    def get_parameter(self, path: str) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def get_index_by_id(self, id: str) -> int:
        if id not in self.entries:
            raise LookupError(f'No entry with id {id}')
        return list(self.entries.keys()).index(id)
