from __future__ import annotations

import os
import sys
import random
import string
import asyncio
import traceback
from typing import TYPE_CHECKING, Any
from dataclasses import dataclass
from pathlib import Path
from contextlib import suppress

from packaging.version import Version

import exit_codes
from loggers import (
    main as logger,
    plugins as plugins_logger,
)

from funpayhub.lib.plugins import PluginManager
from ..plugins.repository.manager import RepositoriesManager
from funpayhub.lib.exceptions import GoodsError
from funpayhub.lib.translater import Translater
from funpayhub.lib.goods_sources import FileGoodsSource, GoodsSourcesManager

from .telegram import TelegramApp
from .workflow_data import WorkflowData

if TYPE_CHECKING:
    from collections.abc import Callable

    from eventry.asyncio.event import Event
    from eventry.asyncio.dispatcher import Dispatcher

    from funpayhub.lib.properties import Node, Properties, MutableParameter


def random_part(length) -> str:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


@dataclass
class AppConfig:
    on_parameter_change_event_factory: Callable[[MutableParameter], Event]
    on_node_attached_event_factory: Callable[[Node], Event]


class App:
    def __init__(
        self,
        version: Version,
        config: AppConfig,
        dispatcher: Dispatcher,
        properties: Properties,
        plugin_manager: PluginManager,
        repositories_manager: RepositoriesManager | None = None,
        translater: Translater | None = None,
        telegram_app: TelegramApp | None = None,
        safe_mode: bool = False,
        telegram_bot_token: str = '',
        workflow_data: WorkflowData | None = None,
    ):
        self._instance_id = '-'.join(map(random_part, [4, 4, 4]))
        self._version = version

        self._config = config
        self._safe_mode = safe_mode
        self._properties = properties
        self._translater = translater or Translater()
        self._goods_manager = GoodsSourcesManager()
        self._plugin_manager = plugin_manager
        self._plugin_manager._safe_mode = self._safe_mode
        self._repositories_manager = repositories_manager if repositories_manager is not None \
            else RepositoriesManager('storage/repositories')

        self._workflow_data = workflow_data if workflow_data is not None else WorkflowData()
        self._dispatcher = dispatcher

        self._telegram = telegram_app or TelegramApp(
            bot_token=telegram_bot_token,
            workflow_data=self.workflow_data,
        )

        self._workflow_data.update(
            {
                'app': self,
                'properties': self.properties,
                'translater': self.translater,
                'tg': self._telegram,
                'tg_dispatcher': self._telegram.dispatcher,
                'tg_dp': self._telegram.dispatcher,
                'tg_bot': self._telegram.bot,
                'tg_ui': self._telegram.ui_registry,
                'tg_ui_registry': self._telegram.ui_registry,
                'plugin_manager': self._plugin_manager,
                'plugins_manager': self._plugin_manager,
                'repositories_manager': self._repositories_manager,
                'goods_manager': self._goods_manager,
            },
        )

        self._setup_lock = asyncio.Lock()
        self._setup_completed = False

        logger.info(
            'App initialized. Version: %s. Instance ID: %s',
            self._version,
            self._instance_id,
        )

    async def setup(self) -> None:
        async with self._setup_lock:
            if self._setup_completed:
                return

            await self._load_file_goods_sources()
            await self._load_plugins()

            self._setup_completed = True

    async def _load_plugins(self) -> None:
        try:
            await self._plugin_manager.load_plugins()
            await self._plugin_manager.setup_plugins()
        except Exception:
            plugins_logger.critical('Failed to load plugins. Creating crashlog.', exc_info=True)
            with suppress(Exception):
                await self.create_crash_log()
            sys.exit(exit_codes.RESTART_SAFE)  # todo: graceful shutdown before start

    async def _load_file_goods_sources(self) -> None:
        logger.info('Loading goods files.')

        base_path = Path('storage/goods')
        if not base_path.exists():
            return

        for file in base_path.iterdir():
            if not file.is_file():
                continue

            if not file.suffix == '.txt':
                continue

            logger.info('Loading goods file %s.', file)

            try:
                await self._goods_manager.add_source(FileGoodsSource, file)
            except GoodsError as e:
                logger.error(
                    'An error occurred while loading goods file %s: %s',
                    file,
                    e.format_args(self.translater.translate(e.message)),
                )

    async def create_crash_log(self) -> None:
        os.makedirs('logs', exist_ok=True)
        with open('logs/crashlog.log', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())

    async def start(self) -> int:
        self._workflow_data.check_ready()
        return 0

    async def shutdown(self, code: int, error_ok: bool = False) -> None:
        raise NotImplementedError()

    async def emit_parameter_changed_event(self, parameter: MutableParameter[Any]) -> None:
        event = self._config.on_parameter_change_event_factory(parameter)
        await self.dispatcher.event_entry(event)

    async def emit_node_attached_event(self, node: Node) -> None:
        event = self._config.on_node_attached_event_factory(node)
        await self.dispatcher.event_entry(event)

    @property
    def version(self) -> Version:
        return self._version

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def properties(self) -> Properties:
        return self._properties

    @property
    def translater(self) -> Translater:
        return self._translater

    @property
    def telegram(self) -> TelegramApp:
        return self._telegram

    @property
    def workflow_data(self) -> WorkflowData:
        return self._workflow_data

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @property
    def goods_managers(self) -> GoodsSourcesManager:
        return self._goods_manager

    @property
    def safe_mode(self) -> bool:
        return self._safe_mode

    @property
    def plugin_manager(self) -> PluginManager:
        return self._plugin_manager

    @property
    def repositories_manager(self) -> RepositoriesManager:
        return self._repositories_manager
