from __future__ import annotations

import os
import asyncio
from typing import Any

from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.properties import Parameter, MutableParameter, Properties
from funpayhub.lib.translater import Translater
from funpayhub.app.funpay.main import FunPay
from funpayhub.app.telegram.main import Telegram

from funpayhub.app.dispatching import Dispatcher as HubDispatcher, ParameterValueChangedEvent, \
    PropertiesAttachedEvent, ParameterAttachedEvent

# plugins
from funpayhub.plugins.exec_plugin import Plugin


class FunPayHub:
    def __init__(
        self,
        properties: FunPayHubProperties | None = None,
    ):
        self._workflow_data = {}
        self._dispatcher = HubDispatcher(workflow_data=self._workflow_data)

        if properties is None:
            properties = FunPayHubProperties()
            properties.load()
        self._properties = properties

        self._translater = Translater()
        self._translater.add_translations('funpayhub/locales')

        self._funpay = FunPay(self, workflow_data=self.workflow_data)
        self._telegram = Telegram(
            self,
            bot_token=os.environ.get('FPH_TELEGRAM_TOKEN'),  # todo: or from config
            workflow_data=self.workflow_data,
            translater=self._translater,
        )

        self.workflow_data.update(
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
            },
        )

    async def start(self):
        tasks = await asyncio.gather(
            # self.funpay.start(),
            self.telegram.start(),
        )

    async def load_plugins(self):
        pl = Plugin()
        await pl.setup(self)

    async def emit_parameter_changed_event(
        self,
        parameter: MutableParameter[Any]
    ) -> None:
        event = ParameterValueChangedEvent(param=parameter)
        await self.dispatcher.propagate_event(event)

    async def emit_properties_attached_event(
        self,
        properties: Properties,
    ) -> None:
        event = PropertiesAttachedEvent(props=properties)
        await self.dispatcher.propagate_event(event)

    async def emit_parameter_attached_event(
        self,
        parameter: Parameter[Any] | MutableParameter[Any],
    ) -> None:
        event = ParameterAttachedEvent(param=parameter)
        await self.dispatcher.propagate_event(event)

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

    @property
    def workflow_data(self) -> dict[str, Any]:
        return self._workflow_data

    @property
    def dispatcher(self) -> HubDispatcher:
        return self._dispatcher
