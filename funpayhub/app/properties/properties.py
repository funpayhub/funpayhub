from __future__ import annotations

from funpayhub.properties import Properties, StringParameter, ToggleParameter
from typing import Any, TypeVar
from .auto_delivery_properties import AutoDeliveryProperties
from .telegram_properties import TelegramProperties


T = TypeVar('T', bound=Properties)


class TogglesProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='toggles',
            name='$props_toggles:name',
            description='$props_toggles:description',
        )

        self.auto_delivery = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_delivery',
            name='$props_toggles.auto_delivery:name',
            description='$props_toggles.auto_delivery:description',
            default_value=True,
        ))

        self.multi_delivery = self.attach_parameter(ToggleParameter(
            properties=self,
            id='multi_delivery',
            name='$props_toggles.multi_delivery:name',
            description='$props_toggles.multi_delivery:description',
            default_value=True,
        ))

        self.auto_response = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_response',
            name='$props_toggles.auto_response:name',
            description='$props_toggles.auto_response:description',
            default_value=True,
        ))

        self.auto_raise = self.attach_parameter(ToggleParameter(
            properties=self,
            id='auto_raise',
            name='$props_toggles.auto_raise:name',
            description='$props_toggles.auto_raise:description',
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
