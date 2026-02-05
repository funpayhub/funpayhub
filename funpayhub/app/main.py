from __future__ import annotations

import os
import sys
import random
import string
import asyncio
import traceback
from typing import TYPE_CHECKING, Any

from colorama import Fore, Style
from aiogram.types import User

import exit_codes
from loggers import main as logger
from funpayhub.app.plugins import PluginManager
from funpayhub.app.routers import ROUTERS
from funpayhub.lib.base_app import App
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.app.dispatching import Dispatcher as HubDispatcher
from funpayhub.app.funpay.main import FunPay
from funpayhub.app.telegram.main import Telegram
from funpayhub.app.workflow_data import WorkflowData
from funpayhub.app.dispatching.events.other_events import FunPayHubStoppedEvent

from .tty import INIT_SETUP_TEXT_EN, INIT_SETUP_TEXT_RU, box_messages


def random_part(length) -> str:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


class FunPayHub(App):
    if TYPE_CHECKING:
        properties: FunPayHubProperties
        telegram: Telegram

    def __init__(
        self,
        properties: FunPayHubProperties,
        translater: Translater | None = None,
        safe_mode: bool = False,
    ):
        self._setup_completed = bool(properties.general.golden_key.value)
        self._workflow_data = WorkflowData
        self._funpay = FunPay(
            self,
            bot_token=properties.general.golden_key.value,
            proxy=properties.general.proxy.value or None,
            headers=None,
            workflow_data=self.workflow_data,
        )

        telegram_app = Telegram(self, os.environ.get('FPH_TELEGRAM_TOKEN'), self._workflow_data)

        self._stop_signal: asyncio.Future[int] = asyncio.Future()
        self._stopped_signal = asyncio.Event()
        self._running_lock = asyncio.Lock()
        self._stopping_lock = asyncio.Lock()

        self._setup_lock = asyncio.Lock()
        self._setup = False

        super().__init__(
            version=properties.version.value,
            config=...,
            dispatcher=HubDispatcher(workflow_data=self._workflow_data),
            properties=properties,
            plugin_manager=PluginManager(self, properties.version),
            translater=translater,
            safe_mode=safe_mode,
            telegram_app=telegram_app
        )

        self._setup_dispatcher()

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
                'goods_manager': self._goods_manager,
            },
        )

    async def setup(self) -> None:
        async with self._setup_lock:
            if self._setup:
                return

            await self._load_file_goods_sources()
            if self.can_load_plugins:
                await self._load_plugins()

            self._setup = True

    def _setup_dispatcher(self) -> None:
        self._dispatcher.connect_routers(*ROUTERS)

    async def create_crash_log(self) -> None:
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

            if not self.setup_completed:
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

    def _welcome_tty(self, me: User) -> None:
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
            ),
        )
        input(
            f'{Fore.GREEN + Style.BRIGHT}'
            f'Press ENTER to continue / Нажмите ENTER чтобы продолжить...'
            f'{Style.RESET_ALL}',
        )
        print('\033[2J\033[H', end='')

    @property
    def funpay(self) -> FunPay:
        return self._funpay

    @property
    def telegram(self) -> Telegram:
        return self._telegram

    @property
    def workflow_data(self) -> dict[str, Any]:
        return self._workflow_data

    @property
    def dispatcher(self) -> HubDispatcher:
        return self._dispatcher

    @property
    def setup_completed(self) -> bool:
        return self._setup_completed

    @property
    def can_load_plugins(self) -> bool:
        return not self.safe_mode and self.setup_completed
