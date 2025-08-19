from __future__ import annotations

from funpayhub.properties import Properties, StringParameter, ToggleParameter
from typing import Any, TypeVar
import tomllib
import os


T = TypeVar('T', bound=Properties)


class TelegramProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='telegram',
            name='Telegram bot properties',
            description='Telegram bot properties',
            file='config/telegram.toml',
        )

        self.token = self.attach_parameter(StringParameter(
            properties=self,
            id='token',
            name='Telegram bot token',
            description='Telegram bot token',
            default_value='',
        ))


class AutoDeliveryEntryProperties(Properties):
    def __init__(
        self,
        offer_name,
    ) -> None:
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


class AutoDeliveryProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='auto_delivery',
            name='Auto delivery',
            description='Auto delivery options',
            file='config/auto_delivery.toml'
        )

    def attach_parameter(self, parameter: Any) -> Any:
        raise RuntimeError('AutoDeliveryProperties does not support parameters.')

    def add_properties(self, properties: T) -> T:
        if not isinstance(properties, AutoDeliveryEntryProperties):
            raise ValueError('AutoDeliveryProperties supports only AutoDeliveryEntryProperties.')
        return super().attach_properties(properties)

    def load(self):
        if not os.path.exists(self.file):
            return
        with open(self.file, 'r', encoding='utf-8') as f:
            data = tomllib.loads(f.read())

        self._entries = {}
        for i in data:
            obj = AutoDeliveryEntryProperties(offer_name=i)
            obj._set_values(data[i])
            self.add_properties(obj)

    def add_entry(self, offer_name: str) -> AutoDeliveryEntryProperties:
        obj = AutoDeliveryEntryProperties(offer_name)
        self.add_properties(obj)
        return obj


class TogglesProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='toggles',
            name='Toggles',
            description='Toggles properties',
        )

        self.auto_delivery = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_delivery',
            name='Auto delivery',
            description='Whether auto delivery is enabled or not.',
            default_value=True,
        ))

        self.multi_delivery = self.attach_parameter(ToggleParameter(
            properties=self,
            id='multi_delivery',
            name='Multi delivery',
            description='Whether multi delivery is enabled or not.',
            default_value=True,
        ))

        self.auto_response = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_response',
            name='Auto response',
            description='Whether auto response is enabled or not.',
            default_value=True,
        ))

        self.auto_raise = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_raise',
            name='Auto raise',
            description='Whether auto raise is enabled or not.',
            default_value=True,
        ))

        self.auto_raise2 = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_raise2',
            name='Auto raise2',
            description='Whether auto raise is enabled or not.',
            default_value=True,
        ))

        self.auto_raise3 = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_raise3',
            name='Auto raise3',
            description='Whether auto raise is enabled or not.',
            default_value=True,
        ))

        self.auto_raise4 = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_raise4',
            name='Auto raise4',
            description='Whether auto raise is enabled or not.',
            default_value=True,
        ))


class FunPayHubProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='funpayhub',
            name='FunPay Hub properties',
            description='FunPay Hub properties.',
            file='config/funpayhub.toml',
        )

        self.toggles = self.attach_properties(TogglesProperties())
        self.telegram = self.attach_properties(TelegramProperties())
        self.auto_delivery = self.attach_properties(AutoDeliveryProperties())


a = FunPayHubProperties()
a.load()

print(a.toggles.auto_delivery.value)
print(a.auto_delivery._entries)