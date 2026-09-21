from __future__ import annotations


__all__ = ['TelegramComponent']

import os

from hubplatform.app import HubPlatformApp
from hubplatform.app.components.telegram import TelegramComponent as BaseTelegramComponent

from .properties import TelegramProperties


class TelegramComponent(BaseTelegramComponent):
    def __init__(self, properties: TelegramProperties):
        telegram_token = os.environ.get('TELEGRAM_TOKEN', properties.bot.token.value)
        super().__init__(token=telegram_token)
        self._properties = properties

    @property
    def properties(self) -> TelegramProperties:
        return self._properties

    async def setup(self, app: HubPlatformApp) -> None:
        app.properties.attach_node(self._properties)
        await super().setup(app)
