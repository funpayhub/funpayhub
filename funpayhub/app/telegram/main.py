from __future__ import annotations

import html
import asyncio
from typing import TYPE_CHECKING
from itertools import chain

from aiogram.types import Message, BotCommand, InlineKeyboardMarkup

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.properties import ListParameter
from funpayhub.lib.translater import _
from funpayhub.lib.base_app.telegram.main import TelegramApp

from funpayhub.app.telegram.ui import default as default_ui
from funpayhub.app.telegram.modules import MENUS, BUTTONS, ROUTERS, MENU_MODS, BUTTON_MODS
from funpayhub.app.dispatching.events import TelegramStartEvent
from funpayhub.app.telegram.middlewares import (
    OopsMiddleware,
    UnpackMiddleware,
    AddDataMiddleware,
    IsAuthorizedMiddleware,
)
from funpayhub.app.notification_channels import NotificationChannels


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.workflow_data import WorkflowData


class Telegram(TelegramApp):
    def __init__(
        self,
        hub: FunPayHub,
        bot_token: str,
        workflow_data: WorkflowData,
    ) -> None:
        self._hub = hub

        super().__init__(
            bot_token=bot_token,
            workflow_data=workflow_data,
        )

        self._setup_commands()

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    def _setup_dispatcher(self) -> None:
        super()._setup_dispatcher()
        self._dispatcher.include_routers(*ROUTERS)

        middleware = AddDataMiddleware()
        for i, o in self.dispatcher.observers.items():
            if i == 'error':
                continue
            o.outer_middleware(middleware)

        self.dispatcher.callback_query.outer_middleware(OopsMiddleware())
        self.dispatcher.callback_query.outer_middleware(UnpackMiddleware())

        _is_authorized_middleware = IsAuthorizedMiddleware()
        self.dispatcher.callback_query.outer_middleware(_is_authorized_middleware)
        self.dispatcher.message.outer_middleware(_is_authorized_middleware)

        # todo
        from funpayhub.app.telegram.modules.help.handlers import NeedHelpMiddleware, router

        self.dispatcher.callback_query.outer_middleware(NeedHelpMiddleware())
        self.dispatcher.include_routers(router)

    def _setup_commands(self) -> None:
        self._commands_registry.create_command('start', 'hub', True, _('Главное меню.'))
        self._commands_registry.create_command('settings', 'hub', True, _('Меню настроек.'))
        self._commands_registry.create_command('help', 'hub', True, _('Режим справки.'))
        self._commands_registry.create_command('shutdown', 'hub', True, _('Завершение работы.'))
        self._commands_registry.create_command('restart', 'hub', True, _('Перезапуск.'))
        self._commands_registry.create_command('safe_mode', 'hub', True, _('Безопасный режим.'))
        self._commands_registry.create_command(
            'standard_mode',
            'hub',
            True,
            _('Стандартный режим.'),
        )

    def _setup_ui(self) -> None:
        super()._setup_ui()
        for m in chain(default_ui.MENU_BUILDERS, MENUS):
            self.ui_registry.add_menu_builder(m)

        for b in chain(default_ui.BUTTON_BUILDERS, BUTTONS):
            self.ui_registry.add_button_builder(b)

        for menu_id, modifications in chain(
            default_ui.MENU_MODIFICATIONS.items(),
            MENU_MODS.items(),
        ):
            for mod in modifications:
                self.ui_registry.add_menu_modification(mod, menu_id)

        for button_id, modifications in BUTTON_MODS.items():
            for mod in modifications:
                self.ui_registry.add_button_modification(mod, button_id)

    async def start(self) -> None:
        commands = [
            BotCommand(
                command=cmd.command,
                description=self.hub.translater.translate(cmd.description),
            )
            for cmd in self._commands_registry.commands(setup_only=True)
        ]
        await self.bot.set_my_commands(commands)
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.hub.dispatcher.event_entry(TelegramStartEvent())
        await self.dispatcher.start_polling(self.bot)

    def send_notification(
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

    def send_error_notification(
        self,
        text: str,
        exception: Exception | None = None,
    ) -> list[asyncio.Task[Message]]:
        if isinstance(exception, TranslatableException):
            exc_text = exception.format_args(self.hub.translater.translate(exception.message))
        else:
            exc_text = self.hub.translater.translate('Подробности в логах.')

        text = text + '\n\n' + html.escape(exc_text)
        return self.send_notification(NotificationChannels.ERROR, text)
