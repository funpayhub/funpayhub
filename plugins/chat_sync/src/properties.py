from funpayhub.lib.properties import Properties, ListParameter, IntParameter


class ChatSyncProperties(Properties):
    def __init__(self):
        super().__init__(
            id='chat_sync',
            name='Chat Sync',
            description='Chat Sync',
            file='config/chat_sync.toml'
        )

        self.sync_chat_id = self.attach_parameter(
            IntParameter(
                id='sync_chat_id',
                name='ID чата синхронизации',
                description='ID чата с темами, в который будут присылаться сообщения.',
                default_value=0
            )
        )

        self.bot_tokens = self.attach_parameter(
            ListParameter(
                id='bot_tokens',
                name='Токены Telegram ботов',
                description='Токены Telegram ботов для отправки сообщений в темы.',
                default_value=[]
            )
        )
