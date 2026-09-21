from __future__ import annotations


__all__ = [
    'FunPayProperties',
]

from pyconfigtree import Properties
from hubplatform.i18n import I18nString
from pyconfigtree.source.toml import TOMLSource


class FunPayProperties(Properties):
    def __init__(self):
        super().__init__(
            node_id='funpay',
            name=I18nString(
                key='funpayhub.properties.funpay_component.name',
                fallback='Компонент FunPay',
            ),
            description=I18nString(
                key='funpayhub.properties.funpay_component.description',
                fallback='Настройки FunPay компонента.',
            ),
            source=TOMLSource('config/funpay.toml'),
            metadata={'emoji': '🔷'},
        )
