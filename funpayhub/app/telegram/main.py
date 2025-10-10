from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.strategy import FSMStrategy

from funpayhub.lib.telegram.callback_data import CallbackData
from funpayhub.lib.telegram.callbacks import MenuPageable, ViewPageable
from funpayhub.lib.telegram.ui import UIContext
from funpayhub.lib.translater import Translater
from funpayhub.app.telegram.ui import default as default_ui
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
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
        translater: Translater,
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

        self._hashinator = HashinatorT1000()
        self._ui_registry = UIRegistry(hashinator=self._hashinator, translater=translater)
        self._setup_ui_defaults()

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
        for t, b in default_ui.DEFAULT_ENTRIES_BUTTONS.items():
            self._ui_registry.add_default_entry_button_builder(t, b)

        for t, m in default_ui.DEFAULT_ENTRIES_MENUS.items():
            self._ui_registry.set_default_entry_menu_builder(t, m)

        for i, m in default_ui.DEFAULT_MENUS.items():
            self._ui_registry.add_menu(i, m)

        for i, b in default_ui.ENTRIES_BUTTONS_MODIFICATIONS.items():
            self._ui_registry.add_entry_button_modification(i, b)

        for i, m in default_ui.ENTRIES_MENUS_MODIFICATIONS.items():
            self._ui_registry.add_entry_menu_modification(i, m)

        # todo: add menus modifications

    async def start(self) -> None:
        await self.dispatcher.start_polling(self.bot)

    def make_ui_context(self, callback_data: CallbackData) -> UIContext:
        menu_page = callback_data.menu_page if isinstance(callback_data, MenuPageable) else 0
        view_page = callback_data.view_page if isinstance(callback_data, ViewPageable) else 0

        return UIContext(
            language=self.hub.properties.general.language.real_value,
            max_elements_on_page=self.hub.properties.telegram.appearance.menu_entries_amount.value,
            menu_page=menu_page,
            view_page=view_page,
            callback=callback_data
        )
