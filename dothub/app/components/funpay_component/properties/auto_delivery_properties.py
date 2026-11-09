from __future__ import annotations


__all__ = ['AutoDeliveryNode', 'AutoDeliveryProperties']


from typing import TYPE_CHECKING, Any

from pyconfigtree import Properties, BoolParameter, StringParameter
from hubplatform.i18n import I18nString
from pyconfigtree.source.toml import TOMLSource


class AutoDeliveryNode(Properties):
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
                name=I18nString('Автовыдача'),
                description=I18nString('nodesc'),
                default_value=True,
            ),
        )

        self.multi_delivery = self.attach_node(
            BoolParameter(
                node_id='multi_delivery',
                name=I18nString('Определять к-во товара'),
                description=I18nString('nodesc'),
                default_value=True,
            ),
        )

        self.goods_source = self.attach_node(
            StringParameter(
                node_id='goods_source',
                name=I18nString('Источник товаров'),
                description=I18nString('nodesc'),
                default_value='',
                metadata={'emoji': '🗳'},
            ),
        )

        self.delivery_text = self.attach_node(
            StringParameter(
                node_id='delivery_text',
                name=I18nString('Текст выдачи'),
                description=I18nString('nodesc'),
                default_value='',
            ),
        )


class AutoDeliveryProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='auto_delivery',
            name=I18nString('Настройки автовыдачи'),
            description=I18nString('nodesc'),
            source=TOMLSource('config/auto_delivery.toml'),
            metadata={'emoji': '📦'},
        )

    async def load_from_dict(
        self,
        data_dict: dict[str, Any],
        validate: bool = True,
        run_hook: bool = False,
    ) -> None:
        for i in data_dict:
            obj = AutoDeliveryNode(offer_name=i)
            await obj.load_from_dict(data_dict[i], validate=validate, run_hook=run_hook)
            self.attach_node(obj)

    async def add_node(self, offer_name: str) -> AutoDeliveryNode:
        return await self.attach_node_with_hooks(AutoDeliveryNode(offer_name))
