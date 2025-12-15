from __future__ import annotations

import os
import random
import string
import asyncio
from typing import Any

from funpayhub.app.routers import ROUTERS
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.properties import Parameter, Properties, MutableParameter
from funpayhub.lib.translater import Translater
from funpayhub.app.dispatching import (
    Dispatcher as HubDispatcher,
    ParameterAttachedEvent,
    PropertiesAttachedEvent,
    ParameterValueChangedEvent,
)
from funpayhub.app.funpay.main import FunPay
from funpayhub.app.telegram.main import Telegram

# plugins
from funpayhub.plugins.exec_plugin import Plugin

from .workflow_data import WorkflowData


random_part = lambda length: ''.join(
    random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
)


class FunPayHub:
    def __init__(
        self,
        properties: FunPayHubProperties,
    ):
        self._instance_id = '-'.join(map(random_part, [4, 4, 4]))
        self._workflow_data = WorkflowData
        self._dispatcher = HubDispatcher(workflow_data=self._workflow_data)
        self.setup_dispatcher()
        self._properties = properties

        self._translater = Translater()
        self._translater.add_translations('funpayhub/locales')

        self._funpay = FunPay(
            self,
            bot_token=os.environ.get('FPH_GOLDEN_KEY'),  # todo: or from properites
            proxy=os.environ.get('FPH_FUNPAY_PROXY'),  # todo: or from properties
            headers=None,
            workflow_data=self.workflow_data,
        )
        self._telegram = Telegram(
            self,
            bot_token=os.environ.get('FPH_TELEGRAM_TOKEN'),  # todo: or from config
            workflow_data=self.workflow_data,
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
                'tg_ui': self.telegram.ui_registry,
            },
        )

        self._running_lock = asyncio.Lock()
        self._stopping_lock = asyncio.Lock()
        self._stop: asyncio.Future[int] = asyncio.Future()

    def setup_dispatcher(self):
        self._dispatcher.connect_routers(*ROUTERS)

    async def start(self) -> int:
        async def wait_future(fut: asyncio.Future) -> None:
            await fut
            print(f'future done: {fut.result()}')

        async with self._running_lock:
            self._stop = asyncio.Future()

            tasks = [
                asyncio.create_task(self.funpay.start(), name='funpay'),
                asyncio.create_task(self.telegram.start(), name='telegram'),
                asyncio.create_task(wait_future(self._stop)),
            ]

            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            async with self._stopping_lock:
                try:
                    await self.funpay.bot.stop_listening()
                except RuntimeError:
                    pass

                try:
                    await self.telegram.dispatcher.stop_polling()
                except RuntimeError:
                    pass

            return self._stop.result()

    async def stop(self, code: int) -> None:
        if self._stopping_lock.locked() or not self._running_lock.locked():
            raise RuntimeError('Already stopped')
        self._stop.set_result(code)

    async def load_plugins(self):
        pl = Plugin()
        await pl.setup(self)
        pass

    async def emit_parameter_changed_event(
        self,
        parameter: MutableParameter[Any],
    ) -> None:
        event = ParameterValueChangedEvent(param=parameter)
        await self.dispatcher.event_entry(event)

    async def emit_properties_attached_event(
        self,
        properties: Properties,
    ) -> None:
        event = PropertiesAttachedEvent(props=properties)
        await self.dispatcher.event_entry(event)

    async def emit_parameter_attached_event(
        self,
        parameter: Parameter[Any] | MutableParameter[Any],
    ) -> None:
        event = ParameterAttachedEvent(param=parameter)
        await self.dispatcher.event_entry(event)

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

    @property
    def instance_id(self) -> str:
        return self._instance_id
