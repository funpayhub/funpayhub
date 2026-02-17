from __future__ import annotations

from typing import Any

from funpayhub.lib.properties import Properties, IntParameter, StringParameter
from funpayhub.lib.translater import _
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag


class FirstResponseProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='first_response',
            name=_('Приветствие'),
            description=_('Настройка ответа на первое сообщение.'),
            file='config/first_response.toml',
            flags=[TelegramUIEmojiFlag('✉️')],
        )

        self.text = self.attach_node(
            StringParameter(
                id='text',
                name=_('Текст приветствия'),
                description=_('Текст, который будет отправлен пользователю при первом сообщении.'),
                default_value='',
                flags=[TelegramUIEmojiFlag('✉️')],
            ),
        )

        self.timeout = self.attach_node(
            IntParameter(
                id='timeout',
                name=_('Время сброса'),
                description=_(
                    'Время в секундах, после которого сообщение от пользователя снова будет считаться новым.',
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
        return f'__offer__{offer_id}' in self._nodes

    def get_offer(self, offer_id: int | str) -> FirstResponseToOfferNode | None:
        return self._nodes.get(f'__offer__{offer_id}')

    async def load_from_dict(self, properties_dict: dict[str, Any]):
        await super().load_from_dict(properties_dict)
        offer_nodes = {k: v for k, v in properties_dict.items() if k.startswith('__offer__')}
        for k, v in offer_nodes.items():
            node = FirstResponseToOfferNode(offer_id=k.lstrip('__offer__'))
            await node.load_from_dict(v)
            self.attach_node(node, replace=True)

    @property
    def has_offer_specific(self) -> bool:
        for i in self._nodes:
            if i.startswith('__offer__') and isinstance(self._nodes[i], FirstResponseToOfferNode):
                return True
        return False


class FirstResponseToOfferNode(Properties):
    def __init__(self, offer_id: str | int):
        super().__init__(
            id='__offer__' + str(offer_id),
            name=str(offer_id),
            description=_('Настройки ответа на первое сообщение для определенного лота.'),
        )

        self.text = self.attach_node(
            StringParameter(
                id='text',
                name=_('Текст приветствия'),
                description=_('Текст, который будет отправлен пользователю при первом сообщении.'),
                default_value='',
                flags=[TelegramUIEmojiFlag('✉️')],
            ),
        )
