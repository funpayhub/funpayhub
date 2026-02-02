from __future__ import annotations

from funpayhub.lib.properties import Properties, IntParameter, SetParameter


class ChatSyncProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='chat_sync',
            name='Chat Sync',
            description='Chat Sync',
            file='config/chat_sync.toml',
        )

        self.sync_chat_id = self.attach_node(
            IntParameter(
                id='sync_chat_id',
                name='ID чата синхронизации',
                description='ID чата с темами, в который будут присылаться сообщения.',
                default_value=0,
            )
        )

        self.bot_tokens = self.attach_node(
            SetParameter[str](
                id='bot_tokens',
                name='Токены Telegram ботов',
                description='Токены Telegram ботов для отправки сообщений в темы.',
            )
        )
