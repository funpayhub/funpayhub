from __future__ import annotations

from pyconfigtree import Node, BoolParameter
from funpayhub.lib.translater import ru, en
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag


class TogglesProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'toggles',
            name=ru('Глобальные переключатели'),
            description=en('nodesc'),
            flags={TelegramUIEmojiFlag('🕹️')},
        )

        self.auto_delivery = self._attach_node(
            BoolParameter(
                'auto_delivery',
                name=ru('Выдача товаров'),
                description=en('nodesc'),
                default_value=True,
            ),
        )

        self.auto_response = self._attach_node(
            BoolParameter(
                'auto_response',
                name=ru('Автоответ'),
                description=en('nodesc'),
                default_value=True,
            ),
        )

        self.auto_raise = self._attach_node(
            BoolParameter(
                'auto_raise',
                name=ru('Поднятие лотов'),
                description=en('nodesc'),
                default_value=True,
            ),
        )
