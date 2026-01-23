from __future__ import annotations

import os
import sys
import random
import string
import asyncio
import traceback
from asyncio import CancelledError
from typing import Any
from contextlib import suppress

import exit_codes
from loggers import main as logger, plugins as plugins_logger
from funpayhub.app.routers import ROUTERS
from funpayhub.lib.plugins import PluginManager
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
from .dispatching.events.other_events import FunPayHubStoppedEvent

from .workflow_data import WorkflowData


def random_part(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


class FunPayHub:
    def __init__(
        self,
        properties: FunPayHubProperties,
        translater: Translater | None = None,
        safe_mode: bool = False,
    ):
        self._instance_id = '-'.join(map(random_part, [4, 4, 4]))
        self._safe_mode = safe_mode
        self._workflow_data = WorkflowData
        self._dispatcher = HubDispatcher(workflow_data=self._workflow_data)
        self.setup_dispatcher()
        self._properties = properties
        self._translater = translater or Translater()
        self._plugin_manager = PluginManager(self)

        self._funpay = FunPay(
            self,
            bot_token=self.properties.general.golden_key.value,
            proxy=self.properties.general.proxy.value or None,
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
                'plugin_manager': self._plugin_manager,
            },
        )

        self._stop_signal = asyncio.Future()
        self._stopped_signal = asyncio.Event()
        self._running_lock = asyncio.Lock()
        self._stopping_lock = asyncio.Lock()
        self._setup_completed = bool(self.properties.general.golden_key.value)

    def setup_dispatcher(self):
        self._dispatcher.connect_routers(*ROUTERS)

    async def load_plugins(self):
        if self.safe_mode:
            return

        try:
            await self._plugin_manager.load_plugins()
            await self._plugin_manager.setup_plugins()
        except Exception:
            plugins_logger.critical('Failed to load plugins. Creating crashlog.', exc_info=True)
            with suppress(Exception):
                await self.create_crash_log()
            await self.shutdown(exit_codes.RESTART_SAFE)

    async def create_crash_log(self):
        os.makedirs('logs', exist_ok=True)
        with open('logs/crashlog.log', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())

    async def start(self) -> int:
        if self._running_lock.locked():
            raise RuntimeError('FunPayHub already running.')

        async def wait_stop_signal() -> None:
            await self._stop_signal

        self._stop_signal = asyncio.Future()
        self._stopped_signal.clear()

        async with self._running_lock:
            tasks = [
                asyncio.create_task(self.telegram.start(), name='telegram'),
                asyncio.create_task(wait_stop_signal(), name='stop_signal'),
            ]
            if self.setup_completed:
                tasks.append(asyncio.create_task(self.funpay.start(), name='funpay'))

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            while True:
                need_to_stop = False
                for i in done:
                    if i.get_name() in ['telegram', 'stop_signal']:
                        need_to_stop = True
                if need_to_stop:
                    break

                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            try:
                async with self._stopping_lock:
                    try:
                        await self.funpay.bot.stop_listening()
                    except RuntimeError:
                        pass

                    try:
                        await self.telegram.dispatcher.stop_polling()
                    except RuntimeError:
                        pass

                    await self.dispatcher.event_entry(FunPayHubStoppedEvent())
            finally:
                self._stopped_signal.set()
                if self._stop_signal.done():
                    return self._stop_signal.result()
                return 1


    async def shutdown(self, code: int, error_ok: bool = False) -> None:
        if not self._running_lock.locked():
            if error_ok:
                return
            raise RuntimeError('FunPayHub is not running.')

        if self._stopping_lock.locked():
            if error_ok:
                return
            raise RuntimeError('FunPayHub is already stopping.')
        if self._stop_signal.done():
            if error_ok:
                return
            raise RuntimeError('FunPayHub is already stopped.')

        logger.info('Shutting down FunPayHub with exit code %d.', code)
        self._stop_signal.set_result(code)
        await self._stopped_signal.wait()

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

    @property
    def safe_mode(self) -> bool:
        return self._safe_mode

    @property
    def setup_completed(self) -> bool:
        return self._setup_completed
