from __future__ import annotations

from typing import Any

from pyconfigtree import Node, BoolParameter
from pyconfigtree.source.toml import TOMLSource
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag


class BlackListNode(Node):
    def __init__(self, username: str):
        super().__init__(
            f'__user__{username}',
            name=username,
            description=username,
        )

        self.auto_delivery = self._attach_node(
            BoolParameter(
                'auto_delivery',
                name='Автовыдача',
                description='Выдавать ли товар данном пользователю?',
                default_value=False,
            ),
        )

        self.auto_response = self._attach_node(
            BoolParameter(
                'block_ar',
                name='Автоответ',
                description='Разрешить ли автоответ для данного пользователя?',
                default_value=False,
            ),
        )

        self.review_reply = self._attach_node(
            BoolParameter(
                'review_reply',
                name='Ответ на отзыв',
                description='Отвечать ли на отзывы данного пользователя?',
                default_value=False,
            ),
        )

        self.review_chat_reply = self._attach_node(
            BoolParameter(
                'review_chat_reply',
                name='Ответ в чат на отзыв',
                description='Отправлять ли ответ на отзыв в чат для данного пользователя?',
                default_value=False,
            ),
        )

    @property
    def username(self) -> str:
        return self.extract_username(self.id)

    @classmethod
    def extract_username(cls, node_id: str) -> str:
        if not cls.is_blacklist_node(node_id):
            raise ValueError('Node is not a blacklist node.')
        return node_id.lstrip('__user__')

    @classmethod
    def username_to_node_id(cls, username: str) -> str:
        return f'__user__{username}'

    @classmethod
    def is_blacklist_node(cls, node_id: str) -> bool:
        return node_id.startswith('__user__')


class BlackList(Node):
    def __init__(self):
        super().__init__(
            'blacklist',
            source=TOMLSource('config/blacklist.toml'),
            flags={TelegramUIEmojiFlag('🚫')},
            name='Черный список',
            description='Черный список пользователей.',
        )

    async def load_from_dict(self, properties_dict: dict[str, Any]) -> None:
        for k, v in properties_dict.items():
            if not BlackListNode.is_blacklist_node(k):
                continue

            node = BlackListNode(BlackListNode.extract_username(k))
            await node.load_from_dict(v)
            if k in self.subnodes:
                self._detach_node(k)
            self._attach_node(node)

    def get_user(self, username: str) -> BlackListNode | None:
        node = self.subnodes.get(BlackListNode.username_to_node_id(username))
        return node if isinstance(node, BlackListNode) else None

    async def add_user(self, username: str, save: bool = True) -> BlackListNode:
        node_id = BlackListNode.username_to_node_id(username)
        if node_id in self.subnodes:
            raise ValueError(f'User {username} already exists in blacklist.')

        node = await self.attach_node(BlackListNode(username))
        if save:
            await self.save()
        return node

    async def del_user(self, username: str, save: bool = True) -> BlackListNode | None:
        node_id = BlackListNode.username_to_node_id(username)
        try:
            node = await self.detach_node(node_id)
        except KeyError:
            node = None
        if save:
            await self.save()
        return node  # type: ignore[return-value]

    def is_ad_disabled_for(self, username: str) -> bool:
        node = self.get_user(username)
        return False if node is None else not node.auto_delivery.value

    def is_ar_disabled_for(self, username: str) -> bool:
        node = self.get_user(username)
        return False if node is None else node.auto_response.value

    def is_rr_disabled_for(self, username: str) -> bool:
        node = self.get_user(username)
        return False if node is None else node.review_reply.value

    def is_rcr_disabled_for(self, username: str) -> bool:
        node = self.get_user(username)
        return False if node is None else node.review_chat_reply.value
