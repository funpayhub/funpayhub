from funpayhub.lib.properties import Properties, ListParameter
from typing_extensions import Any, NoReturn
import os
import tomllib


class NotificationProperties(Properties):
    def __init__(self):
        super(NotificationProperties, self).__init__(
            id='telegram_notifications',
            name='$telegram_notifications:name',
            description='$telegram_notifications:description',
            file='config/notifications.toml'
        )

    def attach_properties(self, properties: Any) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def get_properties(self, path: str) -> NoReturn:
        raise RuntimeError('AutoDeliveryProperties does not support this :(')

    def add_chat(self, chat_id: int, thread_id: int) -> NoReturn:
        parameter = ListParameter(
            properties=self,
            id=f'{chat_id}_{thread_id}',
            name=f'{chat_id}_{thread_id}',
            description=f'{chat_id}_{thread_id}',
            default_value=[],
            value=[]
        )
        self.attach_parameter(parameter)

    def load(self):
        if not os.path.exists(self.file):
            return
        with open(self.file, 'r', encoding='utf-8') as f:
            data = tomllib.loads(f.read())

        self._entries = {}
        for chat_id, value in data.items():
            parameter = ListParameter(
                properties=self,
                id=chat_id,
                name=chat_id,
                description=chat_id,
                default_value=[],
                value=value
            )
            self.attach_parameter(parameter)
