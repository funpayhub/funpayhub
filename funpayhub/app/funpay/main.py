from __future__ import annotations
from typing import TYPE_CHECKING

from funpayhub.lib.hub.text_formatters import FormattersRegistry
from funpayhub.app.formatters import FORMATTERS_LIST

from funpaybotengine import Bot, Dispatcher, AioHttpSession
import os


if TYPE_CHECKING:
    from funpayhub.app.properties.properties import FunPayHubProperties


class FunPay:
    def __init__(self, properties: FunPayHubProperties, workflow_data: dict | None = None):
        workflow_data = workflow_data or {}

        self.text_formatters = FormattersRegistry()
        for i in FORMATTERS_LIST:
            self.text_formatters.add_formatter(i)

        session = AioHttpSession(
            proxy=os.environ.get('FPH_FUNPAY_PROXY'),  # todo: or from properties
        )
        self.bot = Bot(
            golden_key=os.environ.get('FPH_GOLDEN_KEY'),  # todo: or from properites
            session=session
        )

        self.dispatcher = Dispatcher(workflow_data=workflow_data)

    async def start(self):
        await self.bot.listen_events(self.dispatcher)