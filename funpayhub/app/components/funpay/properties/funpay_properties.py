from __future__ import annotations


__all__ = [
    'FunPayProperties',
]

from pyconfigtree import Properties
from hubplatform.i18n import I18nString
from pyconfigtree.source.toml import TOMLSource

from .review_reply import ReviewReplyProperties
from .auto_response import AutoResponseProperties
from .bot_properties import FunPayBotProperties
from .first_response import FirstResponseProperties
from .on_sale_confirmation import OnSaleConfirmation
from .auto_delivery_properties import AutoDeliveryProperties


class FunPayProperties(Properties):
    def __init__(self):
        super().__init__(
            node_id='funpay',
            name=I18nString(
                key='funpayhub.properties.funpay_component.name',
                fallback='FunPay компонент',
            ),
            description=I18nString(
                key='funpayhub.properties.funpay_component.description',
                fallback='Настройки FunPay компонента.',
            ),
            source=TOMLSource('config/funpay/main.toml'),
            metadata={'emoji': '🔷'},
        )

        self.bot_properties = self.attach_node(FunPayBotProperties())
        self.first_response = self.attach_node(FirstResponseProperties())
        self.auto_response = self.attach_node(AutoResponseProperties())
        self.auto_delivery = self.attach_node(AutoDeliveryProperties())
        self.on_sale_confirmation = self.attach_node(OnSaleConfirmation())
        self.review_reply = self.attach_node(ReviewReplyProperties())
