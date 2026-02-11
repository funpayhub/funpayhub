from __future__ import annotations

from funpayhub.lib.properties import Properties, ToggleParameter
from funpayhub.lib.translater import _


class TogglesProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='toggles',
            name=_('🕹️ Глобальные переключатели'),
            description=_('nodesc'),
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
