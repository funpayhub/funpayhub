from __future__ import annotations


__all__ = ['TelegramComponent']

import os
import asyncio

from pyconfigtree import ListParameter
from aiogram.types import Message, InlineKeyboardMarkup
from hubplatform.app import HubPlatformApp
from hubplatform.telegram.ui import MenuContext, MenuEnvironment, MenuDeliveryResult
from hubplatform.app.components.telegram import TelegramComponent as BaseTelegramComponent

from .routers import ROUTER
from .properties import TelegramProperties


class TelegramComponent(BaseTelegramComponent):
    def __init__(self, properties: TelegramProperties):
        telegram_token = os.environ.get('TELEGRAM_TOKEN', properties.bot.token.value)
        super().__init__(token=telegram_token)
        self._properties = properties
        self.dispatcher.include_router(ROUTER)

    @property
    def properties(self) -> TelegramProperties:
        return self._properties

    async def setup(self, app: HubPlatformApp) -> None:
        app.properties.attach_node(self._properties)
        await super().setup(app)

    def send_menu_notification(
        self,
        notification_channel_id: str,
        menu_id: str,
        menu_context: MenuContext,
    ) -> list[asyncio.Task[MenuDeliveryResult]]:
        try:
            chats = self.properties.notifications.get_parameter([notification_channel_id])
            if not isinstance(chats, ListParameter) or not chats.value:
                return []
        except LookupError:
            return []

        tasks = []

        for identifier in chats.value:
            try:
                split = identifier.split('.')
                chat_id, thread_id = int(split[0]), int(split[1]) if split[1].isnumeric() else None
            except IndexError, ValueError:
                continue

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
        notification_channel_id: str,
        text: str,
        keyboard: InlineKeyboardMarkup | None = None,
    ) -> list[asyncio.Task[Message]]:
        try:
            chats = self.properties.notifications.get_parameter([notification_channel_id])
            if not isinstance(chats, ListParameter) or not chats.value:
                return []
        except LookupError:
            return []

        tasks = []
        for identifier in chats.value:
            try:
                split = identifier.split('.')
                chat_id, thread_id = int(split[0]), int(split[1]) if split[1].isnumeric() else None
            except IndexError, ValueError:
                continue

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
