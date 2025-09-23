from __future__ import annotations

from typing import Any, TYPE_CHECKING
from aiogram import Bot, Dispatcher

from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
from funpayhub.lib.translater import Translater
from funpayhub.app.telegram.middlewares.add_data_to_workflow_data import AddDataMiddleware

from funpayhub.app.telegram.middlewares.unhash import UnpackMiddleware


if TYPE_CHECKING:
    from funpayhub.app import FunPayHub


# routers
from funpayhub.app.telegram.routers.properties_menu import router as properties_menu_router


class Telegram:
    def __init__(
        self,
        hub: FunPayHub,
        bot_token: str,
        workflow_data: dict[str, Any],
        translater: Translater
    ) -> None:
        self._hub = hub
        self._dispatcher = Dispatcher()
        self._dispatcher.workflow_data=workflow_data
        self._setup_dispatcher()

        self._bot = Bot(token=bot_token)

        self._hashinator = HashinatorT1000()
        self._ui_registry = UIRegistry(hashinator=self._hashinator, translater=translater)

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @property
    def hashinator(self) -> HashinatorT1000:
        return self._hashinator

    @property
    def ui_registry(self) -> UIRegistry:
        return self._ui_registry

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    def _setup_dispatcher(self):
        self._dispatcher.include_routers(
            properties_menu_router
        )

        middleware = AddDataMiddleware()
        for i, o in self.dispatcher.observers.items():
            if i == 'error':
                continue
            o.outer_middleware(middleware)

        self.dispatcher.callback_query.outer_middleware(UnpackMiddleware())

    async def start(self) -> None:
        await self.dispatcher.start_polling(self.bot)
