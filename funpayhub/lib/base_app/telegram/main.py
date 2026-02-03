from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.default import DefaultBotProperties

from funpayhub.lib.telegram import CommandsRegistry
from funpayhub.lib.telegram.ui.registry import UIRegistry


if TYPE_CHECKING:
    from ..app import App
    from ..workflow_data import WorkflowData


class TelegramApp:
    def __init__(
        self,
        app: App,
        bot_token: str,
        workflow_data: WorkflowData,
        *,
        dispatcher: Dispatcher | None = None,
        commands_registry: CommandsRegistry | None = None,
        ui_registry: UIRegistry | None = None,
    ) -> None:
        self._app = app

        self._dispatcher = dispatcher or Dispatcher(fsm_strategy=FSMStrategy.USER_IN_TOPIC)
        self._dispatcher.workflow_data = workflow_data
        self._commands_registry = commands_registry or CommandsRegistry()
        self._ui_registry = ui_registry or UIRegistry(workflow_data=workflow_data)
        self._bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                disable_notification=False,
                allow_sending_without_reply=True,
                link_preview_is_disabled=True,
            ),
        )

        self._setup_commands()
        self._setup_dispatcher()
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
    def app(self) -> App:
        return self._app

    def _setup_dispatcher(self) -> None: ...

    def _setup_commands(self) -> None:
        self._commands.create_command('start', 'hub', True, '$command:start:description')
        self._commands.create_command('settings', 'hub', True, '$command:settings:description')
        self._commands.create_command('help', 'hub', True, '$commands:help:description')
        self._commands.create_command('shutdown', 'hub', True, '$commands:shutdown:description')
        self._commands.create_command('restart', 'hub', True, '$commands:restart:description')
        self._commands.create_command('safe_mode', 'hub', True, '$commands:safe_mode:description')
        self._commands.create_command(
            'standard_mode',
            'hub',
            True,
            '$commands.standard_mode:description',
        )

    def _setup_ui_defaults(self) -> None:
        pass

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
        # await self.hub.dispatcher.event_entry(TelegramStartEvent())
        await self.dispatcher.start_polling(self.bot)
