from __future__ import annotations

from funpayhub.properties import Properties, StringParameter, ToggleParameter
from typing import Any, TypeVar
from .auto_delivery_properties import AutoDeliveryProperties


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