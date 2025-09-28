from __future__ import annotations

import os
from typing import TYPE_CHECKING

from funpaybotengine import Bot, Dispatcher, AioHttpSession

from funpayhub.app.formatters import FORMATTERS_LIST
from funpayhub.app.funpay.routers import ALL_ROUTERS
from funpayhub.app.funpay import middlewares as mdwr
from funpayhub.lib.hub.text_formatters import FormattersRegistry


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


class FunPay:
    def __init__(self, hub: FunPayHub, workflow_data: dict | None = None):
        workflow_data = workflow_data if workflow_data is not None else {}

        self._hub = hub

        self._text_formatters = FormattersRegistry()
        for i in FORMATTERS_LIST:
            self._text_formatters.add_formatter(i)

        session = AioHttpSession(
            proxy=os.environ.get('FPH_FUNPAY_PROXY'),  # todo: or from properties
        )
        self._bot = Bot(
            golden_key=os.environ.get('FPH_GOLDEN_KEY'),  # todo: or from properites
            session=session,
        )

        self._dispatcher = Dispatcher(workflow_data=workflow_data)
        self.setup_dispatcher()

    async def start(self):
        await self._bot.listen_events(self._dispatcher)

    def setup_dispatcher(self):
        self.dispatcher.on_new_message.outer_middleware.register_middleware(
            mdwr.log_new_message_middleware
        )
        self._dispatcher.connect_routers(*ALL_ROUTERS)

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    @property
    def text_formatters(self) -> FormattersRegistry:
        return self._text_formatters

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher
