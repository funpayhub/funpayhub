from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.strategy import FSMStrategy

from funpayhub.app.telegram.ui import default as default_ui
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.app.telegram.middlewares.unpack_callback import UnpackMiddleware
from funpayhub.app.telegram.middlewares.add_data_to_workflow_data import AddDataMiddleware


if TYPE_CHECKING:
    from funpayhub.app import FunPayHub


# routers
from funpayhub.app.telegram.routers.menu import router as properties_menu_router


class Telegram:
    def __init__(
        self,
        hub: FunPayHub,
        bot_token: str,
        workflow_data: dict[str, Any],
    ) -> None:
        self._hub = hub
        self._dispatcher = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_TOPIC)
        self._dispatcher.workflow_data = workflow_data
        self._setup_dispatcher()

        self._bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                disable_notification=False,
                allow_sending_without_reply=True,
                link_preview_is_disabled=True,
            ),
        )

        self._ui_registry = UIRegistry()
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

    def _setup_dispatcher(self):
        self._dispatcher.include_routers(
            properties_menu_router,
        )

        middleware = AddDataMiddleware()
        for i, o in self.dispatcher.observers.items():
            if i == 'error':
                continue
            o.outer_middleware(middleware)

        self.dispatcher.callback_query.outer_middleware(UnpackMiddleware())

        # todo
        from funpayhub.app.telegram.routers.help.handlers import NeedHelpMiddleware, router
        self.dispatcher.callback_query.outer_middleware(NeedHelpMiddleware())
        self.dispatcher.include_routers(router)

    def _setup_ui_defaults(self):
        for menu_id, (menu_builder, context_type) in default_ui.MENU_BUILDERS.items():
            self.ui_registry.add_menu_builder(menu_id, menu_builder, context_type)

        for button_id, (button_builder, context_type) in default_ui.BUTTON_BUILDERS.items():
            self.ui_registry.add_button_builder(button_id, button_builder, context_type)

        for menu_id, data in default_ui.MENU_MODIFICATIONS.items():
            for mod_id, (filter, modification) in data.items():
                self.ui_registry.add_menu_modification(menu_id, mod_id, modification, filter)

    async def start(self) -> None:
        await self.dispatcher.start_polling(self.bot)
