from __future__ import annotations

from typing import Any

from pyconfigtree import Properties, IntParameter, StringParameter
from hubplatform.i18n import I18nString
from pyconfigtree.source.toml import TOMLSource


class FirstResponseProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='first_response',
            name=I18nString('Приветствие'),
            description=I18nString('Настройка ответа на первое сообщение.'),
            source=TOMLSource('config/funpay/first_response.toml'),
            metadata={'emoji': '✉️'},
        )

        self.text = self.attach_node(
            StringParameter(
                node_id='text',
                name=I18nString('Текст приветствия'),
                description=I18nString(
                    'Текст, который будет отправлен пользователю при первом сообщении.',
                ),
                default_value='',
                metadata={'emoji': '✉️'},
            ),
        )

        self.timeout = self.attach_node(
            IntParameter(
                node_id='timeout',
                name=I18nString('Время сброса'),
                description=I18nString(
                    'Время в секундах, после которого сообщение от пользователя снова будет '
                    'считаться новым.',
                ),
                default_value=86400,
            ),
        )

    async def add_for_offer(
        self,
        offer_id: str | int,
        save: bool = True,
    ) -> FirstResponseToOfferNode:
        node = FirstResponseToOfferNode(offer_id)
        self.attach_node(node)
        if save:
            await self.save()
        return node

    def has_offer(self, offer_id: int | str) -> bool:
        return f'__offer__{offer_id}' in self._persistent_nodes

    def get_offer(self, offer_id: int | str) -> FirstResponseToOfferNode | None:
        return self._persistent_nodes.get(f'__offer__{offer_id}')

    async def load_from_dict(
        self,
        data_dict: dict[str, Any],
        validate: bool = True,
        run_hook: bool = False,
    ) -> None:
        await super().load_from_dict(data_dict=data_dict, validate=validate, run_hook=run_hook)
        offer_nodes = {k: v for k, v in data_dict.items() if k.startswith('__offer__')}
        for k, v in offer_nodes.items():
            obj = FirstResponseToOfferNode(offer_id=k.lstrip('__offer__'))
            await obj.load_from_dict(data_dict[k], validate=validate, run_hook=run_hook)
            self.attach_node(obj)

    @property
    def has_offer_specific(self) -> bool:
        for i in self._persistent_nodes:
            if i.startswith('__offer__') and isinstance(
                self._persistent_nodes[i],
                FirstResponseToOfferNode,
            ):
                return True
        return False


class FirstResponseToOfferNode(Properties):
    def __init__(self, offer_id: str | int):
        super().__init__(
            node_id='__offer__' + str(offer_id),
            name=str(offer_id),
            description=I18nString('Настройки ответа на первое сообщение для определенного лота.'),
        )

        self.text = self.attach_node(
            StringParameter(
                node_id='text',
                name=I18nString('Текст приветствия'),
                description=I18nString(
                    'Текст, который будет отправлен пользователю при первом сообщении.',
                ),
                default_value='',
                metadata={'emoji': '✉️'},
            ),
        )
