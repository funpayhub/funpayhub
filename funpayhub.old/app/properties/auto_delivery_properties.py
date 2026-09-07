from __future__ import annotations

from typing import TYPE_CHECKING, Any
from types import MappingProxyType

from pyconfigtree import Properties, BoolParameter, StringParameter
from pyconfigtree.source.toml import TOMLSource

from funpayhub.lib.translater import en, ru
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag


class AutoDeliveryEntryProperties(Properties):
    if TYPE_CHECKING:
        parent: AutoDeliveryProperties | None

    def __init__(self, offer_name: str) -> None:
        super().__init__(
            node_id=offer_name,
            name=offer_name,
            description=f'Auto delivery options for {offer_name}',
        )

        self.auto_delivery = self.attach_node(
            BoolParameter(
                node_id='auto_delivery',
                name=ru('Автовыдача'),
                description=en('nodesc'),
                default_value=True,
            ),
        )

        self.multi_delivery = self.attach_node(
            BoolParameter(
                node_id='multi_delivery',
                name=ru('Определять к-во товара'),
                description=en('nodesc'),
                default_value=True,
            ),
        )

        self.goods_source = self.attach_node(
            StringParameter(
                node_id='goods_source',
                name=ru('Источник товаров'),
                description=en('nodesc'),
                default_value='',
                flags=[TelegramUIEmojiFlag('🗳')],
            ),
        )

        self.delivery_text = self.attach_node(
            StringParameter(
                node_id='delivery_text',
                name=ru('Текст выдачи'),
                description=en('nodesc'),
                default_value='',
            ),
        )


class AutoDeliveryProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='auto_delivery',
            name=ru('Настройки автовыдачи'),
            description=en('nodesc'),
            source=TOMLSource('config/auto_delivery.toml'),
            flags={TelegramUIEmojiFlag('📦')},
        )

    @property
    def entries(self) -> MappingProxyType[str, AutoDeliveryEntryProperties]:
        return super().entries  # type: ignore

    async def load_from_dict(self, properties_dict: dict[str, Any]) -> None:
        for i in properties_dict:
            obj = AutoDeliveryEntryProperties(offer_name=i)
            await obj.load_from_dict(properties_dict[i])
            self.attach_node(obj, replace=True)

    async def add_node(self, offer_name: str) -> AutoDeliveryEntryProperties:
        return await self.attach_node_and_emit(AutoDeliveryEntryProperties(offer_name))
