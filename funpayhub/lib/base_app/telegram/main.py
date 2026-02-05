from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Update, CallbackQuery
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.default import DefaultBotProperties

from funpayhub.lib.telegram import CommandsRegistry
from funpayhub.lib.telegram.ui.registry import UIRegistry

from .app import MENUS, BUTTONS, ROUTERS
from ...telegram.callback_data import UnknownCallback


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
        dispatcher: Dispatcher | None = None,
        commands_registry: CommandsRegistry | None = None,
        ui_registry: UIRegistry | None = None,
    ) -> None:
        self._config = config if config is not None else TelegramAppConfig()
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

    async def fake_query(
        self,
        callback_data: UnknownCallback | str,
        query: CallbackQuery,
        pack_history: bool = True,
    ) -> None:
        if isinstance(callback_data, UnknownCallback):
            query_str = (
                callback_data.pack_history(hash=False)
                if pack_history
                else callback_data.pack(hash=False)
            )
        else:
            query_str = query

        await self.dispatcher.feed_update(
            self.bot,
            Update(update_id=-1, callback_query=query.model_copy(update={'data': query_str})),
            dispatcher=self.dispatcher,
        )
