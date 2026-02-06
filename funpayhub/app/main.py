from __future__ import annotations

import os
import sys
import random
import string
import asyncio
import traceback
from typing import TYPE_CHECKING

from aiogram.utils.token import TokenValidationError
from colorama import Fore, Style
from aiogram.types import User

import exit_codes
from loggers import main as logger
from funpayhub.app.plugins import PluginManager
from funpayhub.app.routers import ROUTERS
from funpayhub.lib.base_app import App
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.app.dispatching import (
    Dispatcher as HubDispatcher,
    NodeAttachedEvent,
    ParameterValueChangedEvent,
)
from funpayhub.app.funpay.main import FunPay
from funpayhub.lib.base_app.app import AppConfig
from funpayhub.app.telegram.main import Telegram
from funpayhub.app.workflow_data import get_wfd
from funpayhub.app.dispatching.events.other_events import FunPayHubStoppedEvent
from .args_parser import args


if TYPE_CHECKING:
    from .workflow_data import WorkflowData


def random_part(length) -> str:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


class FunPayHub(App):
    if TYPE_CHECKING:
        properties: FunPayHubProperties
        telegram: Telegram
        workflow_data: WorkflowData

    def __init__(
        self,
        properties: FunPayHubProperties,
        translater: Translater | None = None,
        safe_mode: bool = False,
    ):
        self._workflow_data = get_wfd()
        self._funpay = FunPay(
            self,
            bot_token=properties.general.golden_key.value or '__emtpy_golden_key__',
            proxy=properties.general.proxy.value or None,
            headers=None,
            workflow_data=self.workflow_data,
        )

        if args.force_token:
            token = args.force_token
        else:
            token = properties.telegram.general.token.value or args.token

        try:
            telegram_app = Telegram(self, token, self._workflow_data)
        except TokenValidationError:
            sys.exit(exit_codes.TELEGRAM_TOKEN_ERROR)

        self._stop_signal: asyncio.Future[int] = asyncio.Future()
        self._stopped_signal = asyncio.Event()
        self._running_lock = asyncio.Lock()
        self._stopping_lock = asyncio.Lock()

        config = AppConfig(
            on_parameter_change_event_factory=ParameterValueChangedEvent,
            on_node_attached_event_factory=NodeAttachedEvent,
        )

        super().__init__(
            version=properties.version.value,
            config=config,
            dispatcher=HubDispatcher(workflow_data=self._workflow_data),
            properties=properties,
            plugin_manager=PluginManager(self, properties.version.value),
            translater=translater,
            safe_mode=safe_mode,
            telegram_app=telegram_app,
            workflow_data=self.workflow_data,
        )
        self._plugin_manager._disabled_plugins = set(properties.plugin_properties.disabled_plugins.value)

        self._setup_dispatcher()

        self.workflow_data.update(
            {
                'hub': self,
                'funpay': self._funpay,
                'fp': self._funpay,
                'fp_bot': self._funpay.bot,
                'fp_dp': self._funpay.dispatcher,
                'fp_dispatcher': self._funpay.dispatcher,
                'fp_formatters': self._funpay.text_formatters,
                'formatters_registry': self._funpay.text_formatters,
            },
        )

    def _setup_dispatcher(self) -> None:
        self._dispatcher.connect_routers(*ROUTERS)

    async def create_crash_log(self) -> None:
        os.makedirs('logs', exist_ok=True)
        with open('logs/crashlog.log', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())

    async def start(self) -> int:
        await super().start()
        if self._running_lock.locked():
            raise RuntimeError('FunPayHub already running.')

        async def wait_stop_signal() -> None:
            await self._stop_signal

        self._stop_signal = asyncio.Future()
        self._stopped_signal.clear()

        async with self._running_lock:
            try:
                me = await self.telegram.bot.get_me()
            except Exception:
                return exit_codes.TELEGRAM_ERROR

            tasks = [
                asyncio.create_task(self.telegram.start(), name='telegram'),
                asyncio.create_task(wait_stop_signal(), name='stop_signal'),
                asyncio.create_task(self.funpay.start(), name='funpay')
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for i in done:
                if i.exception():
                    raise i.exception()
            while True:
                need_to_stop = False
                for i in done:
                    if i.get_name() in ['telegram', 'stop_signal']:
                        need_to_stop = True
                if need_to_stop:
                    break

                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            exit_code = 1
            if self._stop_signal.done:
                exit_code = self._stop_signal.result()
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

            return exit_code

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

    @property
    def funpay(self) -> FunPay:
        return self._funpay

    @property
    def dispatcher(self) -> HubDispatcher:
        return self._dispatcher
