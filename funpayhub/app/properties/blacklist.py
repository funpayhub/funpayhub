from __future__ import annotations

from typing import Any

from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag
from funpayhub.lib.properties import Properties, ToggleParameter


class BlackListNode(Properties):
    def __init__(self, username: str):
        super().__init__(
            id=f'__user__{username}',
            name=username,
            description=username
        )

        self.auto_delivery = self.attach_node(
            ToggleParameter(
                id='auto_delivery',
                name='Автовыдача',
                description='Выдавать ли товар данном пользователю?',
                default_value=False
            )
        )

        self.auto_response = self.attach_node(
            ToggleParameter(
                id='block_ar',
                name='Автоответ',
                description='Разрешить ли автоответ для данного пользователя?',
                default_value=False
            )
        )

        self.review_reply = self.attach_node(
            ToggleParameter(
                id='review_reply',
                name='Ответ на отзыв',
                description='Отвечать ли на отзывы данного пользователя?',
                default_value=False
            )
        )

        self.review_chat_reply = self.attach_node(
            ToggleParameter(
                id='review_chat_reply',
                name='Ответ в чат на отзыв',
                description='Отправлять ли ответ на отзыв в чат для данного пользователя?',
                default_value=False
            )
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


class BlackList(Properties):
    def __init__(self):
        super().__init__(
            id='blacklist',
            file='config/blacklist.toml',
            flags=[TelegramUIEmojiFlag('🚫')],
            name='Черный список',
            description='Черный список пользователей.'
        )

    async def load_from_dict(self, properties_dict: dict[str, Any]) -> None:
        await super().load_from_dict(properties_dict)
        for k, v in properties_dict.items():
            if not BlackListNode.is_blacklist_node(k):
                continue

            node = BlackListNode(BlackListNode.extract_username(k))
            await node.load_from_dict(v)
            self.attach_node(node, replace=True)

    def get_user(self, username: str) -> BlackListNode | None:
        return self._nodes.get(BlackListNode.username_to_node_id(username))

    async def add_user(self, username: str) -> BlackListNode:
        node_id = BlackListNode.username_to_node_id(username)
        if node_id in self._nodes:
            raise ValueError(f'User {username} already exists in blacklist.')

        return await self.attach_node_and_emit(BlackListNode(username))

    async def del_user(self, username: str) -> BlackListNode | None:
        return await self.detach_node_and_emit(BlackListNode.username_to_node_id(username))

    def is_ad_banned_for(self, username: str) -> bool:
        node = self.get_user(username)
        return False if node is None else not node.auto_delivery.value

    def is_ar_banned_for(self, username: str) -> bool:
        node = self.get_user(username)
        return False if node is None else node.auto_response.value

    def is_rr_banned_for(self, username: str) -> bool:
        node = self.get_user(username)
        return False if node is None else node.review_reply.value

    def is_rcr_banned_for(self, username: str) -> bool:
        node = self.get_user(username)
        return False if node is None else node.review_chat_reply.value
