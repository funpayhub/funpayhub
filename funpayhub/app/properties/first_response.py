from __future__ import annotations

from typing import Any

from pyconfigtree import Node, IntParameter, StringParameter
from pyconfigtree.source.toml import TOMLSource
from funpayhub.lib.translater import ru
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag

from funpayhub.app.properties.flags import FormattersQueryFlag


class FirstResponseProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'first_response',
            name=ru('Приветствие'),
            description=ru('Настройка ответа на первое сообщение.'),
            source=TOMLSource('config/first_response.toml'),
            flags={TelegramUIEmojiFlag('✉️')},
        )

        self.text = self._attach_node(
            StringParameter(
                'text',
                name=ru('Текст приветствия'),
                description=ru('Текст, который будет отправлен пользователю при первом сообщении.'),
                default_value='',
                flags={TelegramUIEmojiFlag('✉️'), FormattersQueryFlag('fph:message|fph:general')},
            ),
        )

        self.timeout = self._attach_node(
            IntParameter(
                'timeout',
                name=ru('Время сброса'),
                description=ru(
                    'Время в секундах, после которого сообщение от пользователя снова будет считаться новым.',
                ),
                default_value=86400,
            ),
        )

    async def add_for_offer(
        self,
        offer_id: str | int,
        save: bool = True,
    ) -> 'FirstResponseToOfferNode':
        node = FirstResponseToOfferNode(offer_id)
        await self.attach_node(node)
        if save:
            await self.save()
        return node

    def has_offer(self, offer_id: int | str) -> bool:
        return f'__offer__{offer_id}' in self.subnodes

    def get_offer(self, offer_id: int | str) -> 'FirstResponseToOfferNode | None':
        node = self.subnodes.get(f'__offer__{offer_id}')
        return node if isinstance(node, FirstResponseToOfferNode) else None

    async def load_from_dict(self, properties_dict: dict[str, Any]):
        offer_nodes = {k: v for k, v in properties_dict.items() if k.startswith('__offer__')}
        for k, v in offer_nodes.items():
            node = FirstResponseToOfferNode(offer_id=k.lstrip('__offer__'))
            await node.load_from_dict(v)
            if k in self.subnodes:
                self._detach_node(k)
            self._attach_node(node)

    @property
    def has_offer_specific(self) -> bool:
        for k, v in self.subnodes.items():
            if k.startswith('__offer__') and isinstance(v, FirstResponseToOfferNode):
                return True
        return False


class FirstResponseToOfferNode(Node):
    def __init__(self, offer_id: str | int):
        super().__init__(
            '__offer__' + str(offer_id),
            name=str(offer_id),
            description=ru('Настройки ответа на первое сообщение для определенного лота.'),
        )

        self.text = self._attach_node(
            StringParameter(
                'text',
                name=ru('Текст приветствия'),
                description=ru('Текст, который будет отправлен пользователю при первом сообщении.'),
                default_value='',
                flags={TelegramUIEmojiFlag('✉️'), FormattersQueryFlag('fph:message|fph:general')},
            ),
        )
