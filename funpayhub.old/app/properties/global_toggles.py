from __future__ import annotations

from dothub.lib.properties import Properties, ToggleParameter
from dothub.lib.translater import _
from dothub.lib.base_app.properties_flags import TelegramUIEmojiFlag


class TogglesProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='toggles',
            name=_('Глобальные переключатели'),
            description=_('nodesc'),
            flags=[TelegramUIEmojiFlag('🕹️')],
        )

        self.auto_delivery = self.attach_node(
            ToggleParameter(
                id='auto_delivery',
                name=_('Выдача товаров'),
                description=_('nodesc'),
                default_value=True,
            ),
        )

        self.auto_response = self.attach_node(
            ToggleParameter(
                id='auto_response',
                name=_('Автоответ'),
                description=_('nodesc'),
                default_value=True,
            ),
        )

        self.auto_raise = self.attach_node(
            ToggleParameter(
                id='auto_raise',
                name=_('Поднятие лотов'),
                description=_('nodesc'),
                default_value=True,
            ),
        )
