from __future__ import annotations

from funpayhub.lib.translater import _


__all__ = [
    'PluginProperties',
]


from typing import TypeVar

from funpayhub.lib.properties import Properties, ListParameter
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag


T = TypeVar('T', bound=Properties)


class PluginProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='plugin_properties',
            name=_('Плагины'),
            description=_('Настройки плагинов.'),
            flags=[TelegramUIEmojiFlag('🧩')],
        )

        self.disabled_plugins = self.attach_node(
            ListParameter(
                id='disabled_plugins',
                name=_('Отключенные плагины'),
                description=_('Список ID отключенных плагинов.'),
                default_factory=list,
                flags=[TelegramUIEmojiFlag('⛔')],
            ),
        )
