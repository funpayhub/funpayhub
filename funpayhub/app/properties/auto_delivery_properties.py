from __future__ import annotations

import os
import tomllib
from typing import TYPE_CHECKING, Any, NoReturn
from types import MappingProxyType

from funpayhub.lib.properties import Properties, StringParameter, ToggleParameter


class AutoDeliveryEntryProperties(Properties):
    def __init__(self, offer_name: str) -> None:
        super().__init__(
            id=offer_name,
            name=offer_name,
            description=f'Auto delivery options for {offer_name}',
        )

        self.auto_delivery = self.attach_parameter(
            ToggleParameter(
                id='auto_delivery',
                name='$props.auto_delivery.*.auto_delivery:name',
                description='$props.auto_delivery.*.auto_delivery:description',
                default_value=True,
            ),
        )

        self.multi_delivery = self.attach_parameter(
            ToggleParameter(
                id='multi_delivery',
                name='$props.auto_delivery.*.multi_delivery:name',
                description='$props.auto_delivery.*.multi_delivery:description',
                default_value=True,
            ),
        )

        self.products_file = self.attach_parameter(
            StringParameter(
                id='products_file',
                name='$props.auto_delivery.*.products_file:name',
                description='$props.auto_delivery.*.products_file:description',
                default_value='',
            ),
        )

        self.delivery_text = self.attach_parameter(
            StringParameter(
                id='delivery_text',
                name='$props.auto_delivery.*.delivery_text:name',
                description='$props.auto_delivery.*.delivery_text:description',
                default_value='Thank you for buying this staff!',
            ),
        )

    if TYPE_CHECKING:

        @property
        def parent(self) -> AutoDeliveryProperties | None: ...

    @Properties.parent.setter
    def parent(self, value: Properties) -> None:
        if not isinstance(value, AutoDeliveryProperties):
            raise TypeError(
                f'{self.__class__.__name__!r} must be attached only to '
                f'{AutoDeliveryProperties.__name__!r}.',
            )
        Properties.parent.__set__(self, value)


class AutoDeliveryProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='auto_delivery',
            name='$props.auto_delivery:name',
            description='$props.auto_delivery:description',
            file='config/auto_delivery.toml',
        )

    @property
    def entries(self) -> MappingProxyType[str, AutoDeliveryEntryProperties]:
        return super().entries  # type: ignore

    def attach_parameter(self, parameter: Any) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support parameters.')

    def attach_properties[P: AutoDeliveryEntryProperties](self, properties: P) -> P:
        if not isinstance(properties, AutoDeliveryEntryProperties):
            raise ValueError(
                f'{self.__class__.__name__!r} allows attaching only for '
                f'{AutoDeliveryEntryProperties.__name__!r} instances.',
            )
        return super().attach_properties(properties)

    async def load(self) -> None:
        if not os.path.exists(self.file):
            return
        with open(self.file, 'r', encoding='utf-8') as f:
            data = tomllib.loads(f.read())

        self._entries = {}
        for i in data:
            obj = AutoDeliveryEntryProperties(offer_name=i)
            await obj._set_values(data[i])
            super().attach_properties(obj)

    def add_entry(self, offer_name: str) -> AutoDeliveryEntryProperties:
        return self.attach_properties(AutoDeliveryEntryProperties(offer_name))
