from __future__ import annotations

from typing import TypeVar

from funpayhub.lib.properties import Properties

from .general_properties import GeneralProperties
from .telegram_properties import TelegramProperties
from .auto_delivery_properties import AutoDeliveryProperties
from .global_toggles import TogglesProperties


T = TypeVar('T', bound=Properties)





class FunPayHubProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='props',
            name='$props:name',
            description='$props:description',
            file='config/funpayhub.toml',
        )

        self.toggles = self.attach_properties(TogglesProperties())
        self.general = self.attach_properties(GeneralProperties())
        self.telegram = self.attach_properties(TelegramProperties())
        self.auto_delivery = self.attach_properties(AutoDeliveryProperties())
