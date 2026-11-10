from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from dothub.lib.plugin import PluginManager
from dothub.lib.properties import Properties
from dothub.lib.translater import Translater
from dothub.lib.telegram.ui import UIRegistry
from dothub.lib.goods_sources import GoodsSourcesManager
from dothub.lib.workflow_data import WorkflowData as BaseWorkflowData
from dothub.lib.hub.text_formatters import FormattersRegistry

from .telegram import TelegramApp
from ..plugin.repository.manager import RepositoriesManager


if TYPE_CHECKING:
    from .app import App


class WorkflowData(BaseWorkflowData):
    if TYPE_CHECKING:
        app: App
        properties: Properties
        translater: Translater
        tg: TelegramApp
        tg_bot: Bot
        tg_dispatcher: Dispatcher
        tg_ui_registry: UIRegistry
        formatters_registry: FormattersRegistry
        goods_manager: GoodsSourcesManager
        plugins_manager: PluginManager
        repositories_manager: RepositoriesManager

    def __init__(self) -> None:
        super().__init__()
        from dothub.lib.base_app import App

        self.check_items.update(
            {
                'app': lambda v: isinstance(v, App),
                'properties': lambda v: isinstance(v, Properties),
                'translater': lambda v: isinstance(v, Translater),
                'tg': lambda v: isinstance(v, TelegramApp),
                'tg_bot': lambda v: isinstance(v, Bot),
                'tg_dispatcher': lambda v: isinstance(v, Dispatcher),
                'tg_ui_registry': lambda v: isinstance(v, UIRegistry),
                'formatters_registry': lambda v: isinstance(v, FormattersRegistry),
                'goods_manager': lambda v: isinstance(v, GoodsSourcesManager),
                'plugins_manager': lambda v: isinstance(v, PluginManager),
                'repositories_manager': lambda v: isinstance(v, RepositoriesManager),
            },
        )
