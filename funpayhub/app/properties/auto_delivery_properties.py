from __future__ import annotations

from typing import TYPE_CHECKING, Any
from types import MappingProxyType

from pyconfigtree import Node, StringParameter, BoolParameter
from pyconfigtree.source.toml import TOMLSource
from funpayhub.lib.translater import ru, en
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag


class AutoDeliveryEntryProperties(Node):
    if TYPE_CHECKING:
        parent: AutoDeliveryProperties | None

    def __init__(self, offer_name: str) -> None:
        super().__init__(
            node_id=offer_name,
            name=offer_name,
            description=f'Auto delivery options for {offer_name}',
        )

        self.auto_delivery = self._attach_node(
            BoolParameter(
                node_id='auto_delivery',
                name=ru('Автовыдача'),
                description=en('nodesc'),
                default_value=True,
            ),
        )

        self.multi_delivery = self._attach_node(
            BoolParameter(
                node_id='multi_delivery',
                name=ru('Определять к-во товара'),
                description=en('nodesc'),
                default_value=True,
            ),
        )

        self.goods_source = self._attach_node(
            StringParameter(
                node_id='goods_source',
                name=ru('Источник товаров'),
                description=en('nodesc'),
                default_value='',
                flags={TelegramUIEmojiFlag('🗳')},
            ),
        )

        self.delivery_text = self._attach_node(
            StringParameter(
                node_id='delivery_text',
                name=ru('Текст выдачи'),
                description=en('nodesc'),
                default_value='',
            ),
        )


class AutoDeliveryProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            node_id='auto_delivery',
            name=ru('Настройки автовыдачи'),
            description=en('nodesc'),
            source=TOMLSource('config/auto_delivery.toml'),
            flags={TelegramUIEmojiFlag('📦')},
        )

    @property
    def subnodes(self) -> MappingProxyType[str, AutoDeliveryEntryProperties]:
        return super().entries  # type: ignore

    async def load_from_dict(
        self,
        data_dict: dict[str, Any],
        validate: bool = True,
        run_hook: bool = False,
    ) -> None:
        for i in data_dict:
            obj = AutoDeliveryEntryProperties(offer_name=i)
            await obj.load_from_dict(data_dict[i])
            if i in self.subnodes:
                self._detach_node(i)
            self._attach_node(obj)

    async def add_node(self, offer_name: str) -> AutoDeliveryEntryProperties:
        return await self.attach_node(AutoDeliveryEntryProperties(offer_name))
