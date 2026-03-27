from __future__ import annotations


__all__ = ['TelegramAppConfig', 'TelegramApp']


from typing import TYPE_CHECKING
from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from funpayhub.lib.telegram import CommandsRegistry
from funpayhub.lib.telegram.ui.registry import (
    UIRegistry,
    ui_registry as global_ui_registry,
)
from funpayhub.lib.telegram.commands_registry import commands_registry as global_commands_registry

from .app import MENUS, BUTTONS, ROUTERS


if TYPE_CHECKING:
    from ..workflow_data import WorkflowData


@dataclass
class TelegramAppConfig:
    max_menu_lines: int = 6


class TelegramApp:
    def __init__(
        self,
        bot_token: str,
        workflow_data: WorkflowData,
        *,
        config: TelegramAppConfig | None = None,
        commands_registry: CommandsRegistry | None = None,
        ui_registry: UIRegistry | None = None,
        proxy: str | None = None,
    ) -> None:
        self._config = config if config is not None else TelegramAppConfig()

        session = AiohttpSession(proxy=proxy)
        self._bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                disable_notification=False,
                allow_sending_without_reply=True,
                link_preview_is_disabled=True,
            ),
            session=session,
        )

        self._dispatcher = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_TOPIC)
        self._dispatcher.workflow_data = workflow_data

        self._commands_registry = commands_registry or global_commands_registry
        self._ui_registry = ui_registry if ui_registry is not None else global_ui_registry

        self._setup_dispatcher()
        self._setup_ui()

    def _setup_dispatcher(self) -> None:
        self.dispatcher.include_routers(*ROUTERS)

    def _setup_ui(self) -> None:
        for i in MENUS:
            self.ui_registry.add_menu_builder(i)

        for i in BUTTONS:
            self.ui_registry.add_button_builder(i)

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
    def config(self) -> TelegramAppConfig:
        return self._config

    async def start(self) -> None:
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dispatcher.start_polling(self.bot)
