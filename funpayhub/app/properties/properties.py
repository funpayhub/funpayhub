from __future__ import annotations

from typing import TypeVar

from funpayhub.lib.properties import Properties, ListParameter

from .review_reply import ReviewReplyProperties
from .auto_response import AutoResponseProperties
from .global_toggles import TogglesProperties
from .general_properties import GeneralProperties
from .telegram_properties import TelegramProperties
from .auto_delivery_properties import AutoDeliveryProperties


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
        self.auto_response = self.attach_properties(AutoResponseProperties())
        self.auto_delivery = self.attach_properties(AutoDeliveryProperties())
        self.review_reply = self.attach_properties(ReviewReplyProperties())
        self.message_templates = self.attach_parameter(ListParameter[str](
            id='message_templates',
            name='$props.message_templates:names',
            description='$props:message_templates:description',
            default_value=[]
        ))