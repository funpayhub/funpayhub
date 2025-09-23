from __future__ import annotations

from funpayhub.app.properties import FunPayHubProperties
from funpayhub.app.funpay.main import FunPay
from funpayhub.app.telegram.main import Telegram
from funpayhub.lib.translater import Translater
import asyncio
import os


class FunPayHub:
    def __init__(
        self,
        properties: FunPayHubProperties | None = None,
    ):
        workflow_data = {}

        if properties is None:
            properties = FunPayHubProperties()
            properties.load()
        self._properties = properties

        self._translater = Translater()
        self._translater.add_translations('funpayhub/locales')

        self._funpay = FunPay(self, workflow_data=workflow_data)
        self._telegram = Telegram(
            self,
            bot_token=os.environ.get('FPH_TELEGRAM_TOKEN'),  # todo: or from config
            workflow_data=workflow_data,
            translater=self._translater
        )

        workflow_data.update(
            {
                'hub': self,
                'properties': self.properties,
                'translater': self.translater,

                'fp': self.funpay,
                'fp_bot': self.funpay.bot,
                'fp_dp': self.funpay.dispatcher,
                'fp_formatters': self.funpay.text_formatters,

                'tg': self._telegram,
                'tg_bot': self._telegram.bot,
                'tg_dp': self.telegram.dispatcher,
                'hashinator': self.telegram.hashinator,
                'tg_ui': self.telegram.ui_registry,
            }
        )

    async def start(self):
        await asyncio.gather(
            # self.funpay.start(),
            self.telegram.start()
        )

    @property
    def properties(self) -> FunPayHubProperties:
        return self._properties

    @property
    def funpay(self) -> FunPay:
        return self._funpay

    @property
    def telegram(self) -> Telegram:
        return self._telegram

    @property
    def translater(self) -> Translater:
        return self._translater
