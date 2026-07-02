from __future__ import annotations

from funpayhub.lib.translater import ru


__all__ = [
    'PluginProperties',
]


from typing import TypeVar

from pyconfigtree import Node, ListParameter
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag


T = TypeVar('T', bound=Node)


class PluginProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'plugin_properties',
            name=ru('Плагины'),
            description=ru('Настройки плагинов.'),
            flags={TelegramUIEmojiFlag('🧩')},
        )

        self.disabled_plugins = self._attach_node(
            ListParameter(
                'disabled_plugins',
                name=ru('Отключенные плагины'),
                description=ru('Список ID отключенных плагинов.'),
                default_factory=list,
                flags={TelegramUIEmojiFlag('⛔')},
            ),
        )
