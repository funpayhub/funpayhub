from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from aiogram import Router as TGRouter
    from funpaybotengine import Router as FPRouter

    from funpayhub.lib.plugin import PluginManifest
    from funpayhub.lib.properties import Properties
    from funpayhub.lib.telegram.ui import (
        MenuBuilder,
        ButtonBuilder,
        MenuModification,
        ButtonModification,
    )
    from funpayhub.lib.hub.text_formatters import Formatter
    from funpayhub.lib.telegram.commands_registry import Command

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.dispatching import Router as HubRouter


class PluginLogger(logging.Logger):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.plugin = None

    def makeRecord(self, *args, **kwargs):
        record = super().makeRecord(*args, **kwargs)
        record.plugin = self.plugin
        return record


class Plugin:
    def __init__(self, manifest: PluginManifest, hub: FunPayHub) -> None:
        self._manifest = manifest
        self._hub = hub

        logger_class = logging.getLoggerClass()
        logging.setLoggerClass(PluginLogger)
        self._logger = logging.getLogger(f'funpayhub.{manifest.plugin_id.replace(".", "_")}')
        self._logger.plugin = self
        logging.setLoggerClass(logger_class)

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    async def pre_setup(self) -> None:
        raise NotImplementedError()

    async def properties(self) -> Properties:
        raise NotImplementedError()

    async def setup_properties(self) -> None:
        raise NotImplementedError()

    async def formatters(self) -> type[Formatter] | list[type[Formatter]] | None:
        raise NotImplementedError()

    async def setup_formatters(self) -> None:
        raise NotImplementedError()

    async def hub_routers(self) -> HubRouter | list[HubRouter]:
        raise NotImplementedError()

    async def setup_hub_routers(self) -> None:
        raise NotImplementedError()

    async def funpay_routers(self) -> FPRouter | list[FPRouter]:
        raise NotImplementedError()

    async def setup_funpay_routers(self) -> None:
        raise NotImplementedError()

    async def telegram_routers(self) -> TGRouter | list[TGRouter]:
        raise NotImplementedError()

    async def setup_telegram_routers(self) -> None:
        raise NotImplementedError()

    async def menus(self) -> type[MenuBuilder] | list[type[MenuBuilder]]:
        raise NotImplementedError()

    async def setup_menus(self) -> None:
        raise NotImplementedError()

    async def buttons(self) -> type[ButtonBuilder] | list[type[ButtonBuilder]]:
        raise NotImplementedError()

    async def setup_buttons(self) -> None:
        raise NotImplementedError()

    async def menu_modifications(
        self,
    ) -> dict[str, type[MenuModification] | list[type[MenuModification]]]:
        raise NotImplementedError()

    async def setup_menu_modifications(self) -> None:
        raise NotImplementedError()

    async def button_modifications(
        self,
    ) -> dict[str, type[ButtonModification] | list[type[ButtonModification]]]:
        raise NotImplementedError()

    async def setup_button_modifications(self) -> None:
        raise NotImplementedError()

    async def commands(self) -> Command | list[Command] | None:
        raise NotImplementedError()

    async def setup_commands(self) -> None:
        raise NotImplementedError()

    async def post_setup(self) -> None:
        raise NotImplementedError()

    @property
    def logger(self) -> logging.Logger:
        return self._logger
