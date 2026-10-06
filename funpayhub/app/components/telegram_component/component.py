from __future__ import annotations


__all__ = ['TelegramComponent']

import os
import asyncio
from collections.abc import Sequence

from aiogram.types import Message, InlineKeyboardMarkup
from hubplatform.app import HubPlatformApp
from hubplatform.telegram.ui import MenuContext, MenuEnvironment, MenuDeliveryResult
from hubplatform.app.components.telegram import TelegramComponent as BaseTelegramComponent

from .properties import TelegramProperties
from .components.commands import router as commands_router
from .components.main_menu_ui import registry as main_menu_ui_registry
from .components.notifications_ui import (
    router as notifications_ui_router,
    registry as notifications_ui_registry,
)


class TelegramComponent(BaseTelegramComponent):
    def __init__(self, properties: TelegramProperties):
        telegram_token = os.environ.get('TELEGRAM_TOKEN', properties.bot.token.value)
        super().__init__(token=telegram_token)
        self._properties = properties
        self.dispatcher.include_routers(
            commands_router,
            notifications_ui_router,
        )
        self.ui_registry.merge_from(
            notifications_ui_registry,
            main_menu_ui_registry,
        )

    @property
    def properties(self) -> TelegramProperties:
        return self._properties

    async def setup(self, app: HubPlatformApp) -> None:
        app.properties.attach_node(self._properties)
        app.app_context.provide(self.component_name, 'telegram_properties', self._properties)
        app.app_context.provide(self.component_name, 'telegram_component', self)
        await super().setup(app)

    def send_menu_notification(
        self,
        notifications_channel_path: Sequence[str],
        menu_id: str,
        menu_context: MenuContext,
    ) -> list[asyncio.Task[MenuDeliveryResult]]:
        try:
            channel = self.properties.notifications.get_channel(
                notifications_channel_path,
                from_root=True,
            )
        except LookupError:
            return []

        tasks = []

        for chat_id, thread_id in channel.chats:
            tasks.append(
                asyncio.create_task(
                    self.ui_manager.open_menu(
                        menu_id=menu_id,
                        context=menu_context,
                        environment=MenuEnvironment(chat_id=chat_id, thread_id=thread_id),
                        bot=self._bot,
                    ),
                ),
            )

        return tasks

    def send_notification(
        self,
        notifications_channel_path: Sequence[str],
        text: str,
        keyboard: InlineKeyboardMarkup | None = None,
    ) -> list[asyncio.Task[Message]]:
        try:
            channel = self.properties.notifications.get_channel(
                notifications_channel_path,
                from_root=True,
            )
        except LookupError:
            return []

        tasks = []
        for chat_id, thread_id in channel.chats:
            tasks.append(
                asyncio.create_task(
                    self.bot.send_message(
                        chat_id=chat_id,
                        message_thread_id=thread_id,
                        text=text,
                        reply_markup=keyboard,
                    ),
                ),
            )

        return tasks
