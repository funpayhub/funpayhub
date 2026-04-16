from __future__ import annotations
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