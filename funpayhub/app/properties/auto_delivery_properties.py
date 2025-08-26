from __future__ import annotations

from typing import NoReturn, Any

from funpayhub.properties import Properties, ToggleParameter, StringParameter
from funpayhub.properties.base import Entry
import os
from types import MappingProxyType
import tomllib


class AutoDeliveryEntryProperties(Properties):
    def __init__(self, offer_name: str) -> None:
        super().__init__(
            id=offer_name,
            name=offer_name,
            description=f'Auto delivery options for {offer_name}'
        )

        self.auto_delivery = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_delivery',
            name='Auto delivery',
            description='Auto delivery enabled',
            default_value=True
        ))

        self.multi_delivery = self.attach_parameter(ToggleParameter(
            properties=self,
            id='multi_delivery',
            name='Multi delivery',
            description='Multi delivery enabled',
            default_value=True
        ))

        self.products_file = self.attach_parameter(StringParameter(
            properties=self,
            id='products_file',
            name='Products file',
            description='Products file path',
            default_value='',
        ))

        self.delivery_text = self.attach_parameter(StringParameter(
            properties=self,
            id='delivery_text',
            name='Delivery text',
            description='Delivery text',
            default_value='Thank you for buying this staff!'
        ))

    @property
    def parent(self) -> AutoDeliveryProperties | None:
        return super().parent  # type: ignore

    @parent.setter
    def parent(self, value: Properties) -> None:
        if not isinstance(value, AutoDeliveryProperties):
            raise RuntimeError
        Properties.parent.fset(self, value)

    @property
    def path(self) -> str:
        if not self.parent:
            return ''

        id = self.parent.get_index_by_id(self.id)
        return self.parent.path + (f'.{id}' if self.parent.path else str(id))



class AutoDeliveryProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='auto_delivery',
            name='Auto delivery',
            description='Auto delivery options',
            file='config/auto_delivery.toml'
        )

    @property
    def entries(self) -> MappingProxyType[str, AutoDeliveryEntryProperties]:
        return super().entries  # type: ignore

    def attach_parameter(self, parameter: Any) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support parameters.')

    def unattach_parameter(self, id: str) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def attach_properties(self, properties: Any) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def unattach_properties(self, id: str) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def load(self):
        if not os.path.exists(self.file):
            return
        with open(self.file, 'r', encoding='utf-8') as f:
            data = tomllib.loads(f.read())

        self._entries = {}
        for i in data:
            obj = AutoDeliveryEntryProperties(offer_name=i)
            obj._set_values(data[i])
            super().attach_properties(obj)

    def add_entry(self, offer_name: str) -> AutoDeliveryEntryProperties:
        obj = AutoDeliveryEntryProperties(offer_name)
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