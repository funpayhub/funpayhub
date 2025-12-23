from __future__ import annotations

import json
import asyncio
import os.path
from typing import TYPE_CHECKING, Any

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, BotCommand, InlineKeyboardMarkup
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.default import DefaultBotProperties

from funpayhub.app.setup import MENUS, TG_ROUTERS
from funpayhub.lib.telegram import CommandsRegistry
from funpayhub.lib.properties import ListParameter
from funpayhub.app.telegram.ui import default as default_ui
from funpayhub.app.telegram.routers import ROUTERS
from funpayhub.app.dispatching.events import TelegramStartEvent
from funpayhub.app.telegram.middlewares import (
    UnpackMiddleware,
    AddDataMiddleware,
    IsAuthorizedMiddleware,
)
from funpayhub.lib.telegram.ui.registry import UIRegistry


if TYPE_CHECKING:
    from funpayhub.app import FunPayHub


class Telegram:
    def __init__(
        self,
        hub: FunPayHub,
        bot_token: str,
        workflow_data: dict[str, Any],
    ) -> None:
        self._hub = hub
        self._commands = CommandsRegistry()
        self._setup_commands()
        self._dispatcher = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_TOPIC)
        self._dispatcher.workflow_data = workflow_data
        self._setup_dispatcher()

        self._authorized_users: frozenset[int] = frozenset()
        self._load_authorized_users()

        self._bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                disable_notification=False,
                allow_sending_without_reply=True,
                link_preview_is_disabled=True,
            ),
        )

        self._ui_registry = UIRegistry(workflow_data=self.hub.workflow_data)
        self._setup_ui_defaults()

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @property
    def ui_registry(self) -> UIRegistry:
        return self._ui_registry

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    @property
    def authorized_users(self) -> frozenset[int]:
        return self._authorized_users

    def _setup_dispatcher(self):
        self._dispatcher.include_routers(*TG_ROUTERS)  # todo: remove
        self._dispatcher.include_routers(*ROUTERS)

        middleware = AddDataMiddleware()
        for i, o in self.dispatcher.observers.items():
            if i == 'error':
                continue
            o.outer_middleware(middleware)

        self.dispatcher.callback_query.outer_middleware(UnpackMiddleware())

        _is_authorized_middleware = IsAuthorizedMiddleware()
        self.dispatcher.callback_query.outer_middleware(_is_authorized_middleware)
        self.dispatcher.message.outer_middleware(_is_authorized_middleware)

        # todo
        from funpayhub.app.telegram.routers.help.handlers import NeedHelpMiddleware, router

        self.dispatcher.callback_query.outer_middleware(NeedHelpMiddleware())
        self.dispatcher.include_routers(router)

    def _setup_commands(self):
        self._commands.create_command('start', 'hub', True, '$command:start:description')
        self._commands.create_command('help', 'hub', True, '$commands:help:description')

    def _setup_ui_defaults(self):
        for m in default_ui.MENU_BUILDERS:
            self.ui_registry.add_menu_builder(m)

        for m in MENUS:
            self._ui_registry.add_menu_builder(m)

        for b in default_ui.BUTTON_BUILDERS:
            self.ui_registry.add_button_builder(b)

        for menu_id, modifications in default_ui.MENU_MODIFICATIONS.items():
            for mod in modifications:
                self.ui_registry.add_menu_modification(mod, menu_id)

    def _load_authorized_users(self) -> None:
        if not os.path.exists('storage/tg_authorized.json'):
            self._authorized_users = frozenset()
            return

        with open('storage/tg_authorized.json', 'r', encoding='utf-8') as f:
            try:
                self._authorized_users = frozenset(json.loads(f.read()))
            except:
                self._authorized_users = frozenset()

    def authorize_user(self, user_id: int) -> None:
        self._authorized_users |= {user_id}
        with open(os.path.join('storage', 'tg_authorized.json'), 'w', encoding='utf-8') as f:
            json.dump(tuple(self._authorized_users), f, indent=2)

    def deauthorize_user(self, user_id: int) -> None:
        self._authorized_users -= {user_id}
        with open(os.path.join('storage', 'tg_authorized.json'), 'w', encoding='utf-8') as f:
            json.dump(tuple(self._authorized_users), f, indent=2)

    async def start(self) -> None:
        commands = [
            BotCommand(
                command=cmd.command,
                description=self.hub.translater.translate(cmd.description),
            )
            for cmd in self._commands.commands(setup_only=True)
        ]
        await self.bot.set_my_commands(commands)
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.hub.dispatcher.event_entry(TelegramStartEvent())
        await self.dispatcher.start_polling(self.bot)

    async def send_notification(
        self,
        notification_channel_id: str,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> list[asyncio.Task[Message]]:
        """
        Отправляет уведомления во все чаты, которые подписаны на указанный канал уведомлений
        (параметр `notification_channel_id`).

        :param notification_channel_id: Канал уведомлений.
        :param text: Текст уведомления.
        :param reply_markup: Клавиатура уведомления.
        :return: Список объектов `asyncio.Task`.
        """
        try:
            chats = self.hub.properties.telegram.notifications.get_parameter(
                [notification_channel_id],
            )
            if not isinstance(chats, ListParameter) or not chats.value:
                return []
        except LookupError:
            return []

        tasks = []
        for identifier in chats.value:
            try:
                split = identifier.split('.')
                chat_id, thread_id = int(split[0]), int(split[1]) if split[1].isnumeric() else None
            except (IndexError, ValueError):
                continue

            tasks.append(
                asyncio.create_task(
                    self.bot.send_message(
                        chat_id=chat_id,
                        message_thread_id=thread_id,
                        text=text,
                        reply_markup=reply_markup,
                    ),
                ),
            )

        return tasks
