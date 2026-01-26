from __future__ import annotations

import os
import sys
import random
import string
import asyncio
import traceback
from typing import Any
from contextlib import suppress

from colorama import Fore, Style
from aiogram.types import User

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
from funpayhub.lib.goods_sources import GoodsSourcesManager, FileGoodsSource
from pathlib import Path

from .tty import INIT_SETUP_TEXT_EN, INIT_SETUP_TEXT_RU, box_messages
from .workflow_data import WorkflowData
from .dispatching.events.other_events import FunPayHubStoppedEvent
from ..lib.exceptions import GoodsError


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
        logger.info('FunPay Hub initialized. Instance ID: %s', self._instance_id)

        self._setup_completed = bool(properties.general.golden_key.value)
        self._safe_mode = safe_mode
        self._properties = properties
        self._translater = translater or Translater()
        self._goods_manager = GoodsSourcesManager()
        self._plugin_manager = PluginManager(self)

        self._workflow_data = WorkflowData
        self._dispatcher = HubDispatcher(workflow_data=self._workflow_data)
        self._setup_dispatcher()

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
                'goods_manager': self._goods_manager
            },
        )

        self._stop_signal = asyncio.Future()
        self._stopped_signal = asyncio.Event()
        self._running_lock = asyncio.Lock()
        self._stopping_lock = asyncio.Lock()

        self._setup_lock = asyncio.Lock()
        self._setup = False

    async def setup(self) -> None:
        async with self._setup_lock:
            if self._setup:
                return

            await self._load_file_goods_sources()
            if self.can_load_plugins:
                await self._load_plugins()

            self._setup = True

    def _setup_dispatcher(self):
        self._dispatcher.connect_routers(*ROUTERS)

    async def _load_plugins(self):
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

    async def _load_file_goods_sources(self):
        logger.info('Loading goods files.')

        base_path = Path('storage/goods')
        if not base_path.exists():
            return

        for file in base_path.iterdir():
            file: Path

            if not file.is_file():
                continue

            if not file.suffix == '.txt':
                continue

            logger.info('Loading goods file %s.', file)

            try:
                await self._goods_manager.add_source(FileGoodsSource, file)
            except GoodsError as e:
                logger.error(
                    f'An error occurred while loading goods file %s: %s',
                    file,
                    e.format_args(self.translater.translate(e.message))
                )

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
            try:
                me = await self.telegram.bot.get_me()
            except Exception:
                return exit_codes.TELEGRAM_ERROR

            if not self.can_load_plugins:
                if not sys.stdin.isatty() or not sys.stdout.isatty():
                    return exit_codes.NOT_A_TTY

            tasks = [
                asyncio.create_task(self.telegram.start(), name='telegram'),
                asyncio.create_task(wait_stop_signal(), name='stop_signal'),
            ]
            if self.setup_completed:
                tasks.append(asyncio.create_task(self.funpay.start(), name='funpay'))
            else:
                self._welcome_tty(me)

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
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

    def _welcome_tty(self, me: User):
        print('\033[2J\033[H', end='')
        print(
            box_messages(
                INIT_SETUP_TEXT_EN.format(
                    setup_key=self._instance_id,
                    bot_username=me.username,
                ),
                INIT_SETUP_TEXT_RU.format(
                    setup_key=self._instance_id,
                    bot_username=me.username,
                ),
            )
        )
        input(
            f'{Fore.GREEN + Style.BRIGHT}'
            f'Press ENTER to continue / Нажмите ENTER чтобы продолжить...'
            f'{Style.RESET_ALL}',
        )
        print('\033[2J\033[H', end='')

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
    def goods_managers(self) -> GoodsSourcesManager:
        return self._goods_manager

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def safe_mode(self) -> bool:
        return self._safe_mode

    @property
    def setup_completed(self) -> bool:
        return self._setup_completed

    @property
    def can_load_plugins(self) -> bool:
        return not self.safe_mode and self.setup_completed
