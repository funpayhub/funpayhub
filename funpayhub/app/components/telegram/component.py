from __future__ import annotations


__all__ = ['TelegramProperties']

from hubplatform.app.components.telegram import TelegramComponent as BaseTelegramComponent

from .properties import TelegramProperties


class TelegramComponent(BaseTelegramComponent):
    def __init__(self, properties: TelegramProperties):
        super().__init__(token=properties.bot.token)

        self._properties = properties

    @property
    def properties(self) -> TelegramProperties:
        return self._properties
