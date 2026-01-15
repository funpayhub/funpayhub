from __future__ import annotations

__all__ = ['PluginManager']


from collections.abc import Callable, Awaitable
from typing import TYPE_CHECKING
from types import MappingProxyType
from pathlib import Path
from packaging.version import Version
import sys
from typing import Any
import os
import keyword
import importlib
from contextlib import suppress
from .types import PluginManifest, Plugin, LoadedPlugin
from funpayhub.app.dispatching import Router as HUBRouter, Dispatcher as HUBDispatcher
from funpaybotengine import Router as FPRouter, Dispatcher as FPDispatcher
from aiogram import Router as TGRouter, Dispatcher as TGDispatcher
from funpayhub.lib.telegram.ui import MenuBuilder, MenuModification, ButtonBuilder, ButtonModification

if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


class PluginManager:
    PLUGINS_PATH = Path(os.getcwd()) / 'plugins'
    DEV_PLUGINS_PATH = Path(os.environ.get('PYTHONPATH', os.getcwd())) / 'plugins'

    def __init__(self, hub: FunPayHub):
        self._disabled_plugins: set[str] = set()
        self._plugins: dict[str, LoadedPlugin] = {}
        self._hub = hub

        paths = [str(self.DEV_PLUGINS_PATH), str(self.PLUGINS_PATH)]
        for i in paths:
            if i not in sys.path:
                sys.path.append(i)

    def load_disabled_plugins(self, path: str) -> None:
        with open(path, 'r', encoding='utf-8') as f:
            for i in f.read().splitlines():
                if not i:
                    continue
                self._disabled_plugins.add(i)

    def disable_plugin(self, plugin_id: str) -> None:
        if not plugin_id:
            return

        self._disabled_plugins.add(plugin_id)

        with open('disabled_plugins', 'w', encoding='utf-8') as f:
            f.write('\n'.join(self._disabled_plugins))

    def enable_plugin(self, plugin_id: str) -> None:
        if not plugin_id:
            return

        self._disabled_plugins.discard(plugin_id)

        with open('disabled_plugins', 'w', encoding='utf-8') as f:
            f.write('\n'.join(self._disabled_plugins))

    def load_plugin(self, plugin_path: str | Path) -> None:
        module_name = Path(plugin_path).name
        if not module_name.isidentifier() or keyword.iskeyword(module_name):
            return # todo

        try:
            manifest = self._load_plugin_manifest(plugin_path)
        except:
            return # todo

        if manifest.plugin_id in self._disabled_plugins:
            return  # todo: log

        if manifest.plugin_id in self._plugins:
            return # todo: log

        if Version(self.hub.properties.version.value) not in manifest.hub_version:
            return # todo

        try:
            plugin_instance = self._load_entry_point(plugin_path, manifest)
        except:
            return # todo: log

        plugin = LoadedPlugin(manifest=manifest, plugin=plugin_instance)
        self._plugins[manifest.plugin_id] = plugin

    async def setup_plugins(self):
        steps: dict[str, Callable[[LoadedPlugin], Awaitable[Any]]] = {
            'pre_setup': self._run_pre_setup_step,
            'apply_properties': self._apply_properties,
            'setup_properties': self._run_setup_properties_step,
            'apply_hub_routers': self._apply_hub_routers,
            'setup_hub_routers': self._run_setup_hub_routers_step,
            'apply_fp_routers': self._apply_funpay_routers,
            'setup_fp_routers': self._run_setup_funpay_routers_step,
            'apply_tg_routers': self._apply_telegram_routers,
            'setup_tg_routers': self._run_setup_telegram_routers_step,
            'apply_menus': self._apply_menus,
            'setup_menus': self._run_setup_menus_step,
            'apply_menu_modifications': self._apply_menu_modifications,
            'setup_menu_modifications': self._run_setup_menu_modifications_step,
            'apply_buttons': self._apply_buttons,
            'setup_buttons': self._run_setup_buttons_step,
            'apply_button_modifications': self._apply_button_modifications,
            'setup_button_modifications': self._run_setup_button_modifications_step,
            'post_setup': self._run_post_setup
        }

        for name, step in steps.items():
            for plugin_id, plugin in self._plugins.items():
                # todo: logging
                try:
                    await step(plugin)
                except:
                    # todo logging
                    raise # todo PluginLoadError from e

    def _load_plugin_manifest(self, plugin_path: str | Path) -> PluginManifest:
        if not (plugin_path / 'manifest.json').exists():
            raise FileNotFoundError()

        with open(plugin_path / 'manifest.json', 'r', encoding='utf-8') as f:
            return PluginManifest.model_validate_json(f.read())

    def _load_entry_point(
        self,
        plugin_path: str | Path,
        manifest: PluginManifest
    ) -> Plugin:
        plugin_module_name = Path(plugin_path).name
        module_name, class_name = manifest.entry_point.rsplit('.', 1)

        module = importlib.import_module(f'{plugin_module_name}.{module_name}')
        plugin_class: type[Plugin] | None = getattr(module, class_name, None)

        if plugin_class is None:
            raise Exception()  # todo

        if not issubclass(plugin_class, Plugin):
            raise Exception()  # todo

        return plugin_class(manifest, self._hub)


    async def _run_pre_setup_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.pre_setup)

    async def _apply_properties(self, plugin: LoadedPlugin) -> None:
        try:
            properties = await plugin.plugin.properties()
        except NotImplementedError:
            return

        self.hub.properties.attach_properties(properties)
        await self.hub.properties.load()
        self.plugins[plugin.manifest.plugin_id].properties = properties

    async def _run_setup_properties_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.setup_properties)
        await self.hub.properties.load()

    async def _apply_hub_routers(self, plugin: LoadedPlugin) -> None:
        try:
            routers = await plugin.plugin.hub_routers()
        except NotImplementedError:
            return

        if isinstance(routers, HUBRouter):
            routers = [routers]
        elif isinstance(routers, HUBDispatcher):
            raise TypeError('Plugin router cannot be a Dispatcher.')
        elif not isinstance(routers, list):
            raise TypeError('Plugin.hub_routers must return a `Router` or a list of `Router`.')

        self.hub.dispatcher.connect_routers(*routers)

    async def _run_setup_hub_routers_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.setup_hub_routers)

    async def _apply_funpay_routers(self, plugin: LoadedPlugin) -> None:
        try:
            routers = await plugin.plugin.funpay_routers()
        except NotImplementedError:
            return

        if isinstance(routers, FPRouter):
            routers = [routers]
        elif isinstance(routers, FPDispatcher):
            raise TypeError('Plugin router cannot be a Dispatcher.')
        elif not isinstance(routers, list):
            raise TypeError('Plugin.hub_routers must return a `Router` or a list of `Router`.')

        self.hub.funpay.dispatcher.connect_routers(*routers)

    async def _run_setup_funpay_routers_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.setup_funpay_routers)

    async def _apply_telegram_routers(self, plugin: LoadedPlugin) -> None:
        try:
            routers = await plugin.plugin.telegram_routers()
        except NotImplementedError:
            return

        if isinstance(routers, TGRouter):
            routers = [routers]
        elif isinstance(routers, TGDispatcher):
            raise TypeError('Plugin router cannot be a Dispatcher.')
        elif not isinstance(routers, list):
            raise TypeError('Plugin.hub_routers must return a `Router` or a list of `Router`.')

        self.hub.telegram.dispatcher.include_routers(*routers)

    async def _run_setup_telegram_routers_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.setup_telegram_routers)

    async def _apply_menus(self, plugin: LoadedPlugin) -> None:
        try:
            menus = await plugin.plugin.menus()
        except NotImplementedError:
            return

        if isinstance(menus, type) and issubclass(menus, MenuBuilder):
            menus = [menus]
        elif not isinstance(menus, list):
            raise TypeError('Plugin.menus must return a `MenuBuilder` type or a list of `MenuBuilder` types.')

        for i in menus:
            if not isinstance(i, type) or not issubclass(i, MenuBuilder):
                raise TypeError('Plugin.menus must return a `MenuBuilder` type or a list of `MenuBuilder` types.')

            self.hub.telegram.ui_registry.add_menu_builder(i)

    async def _run_setup_menus_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.setup_menus)

    async def _apply_menu_modifications(self, plugin: LoadedPlugin) -> None:
        try:
            modifications = await plugin.plugin.menu_modifications()
        except NotImplementedError:
            return

        for menu_id, modifications_list in modifications.items():
            for i in modifications_list:
                self.hub.telegram.ui_registry.add_menu_modification(i, menu_id)

    async def _run_setup_menu_modifications_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.setup_menu_modifications)

    async def _apply_buttons(self, plugin: LoadedPlugin) -> None:
        try:
            buttons = await plugin.plugin.buttons()
        except NotImplementedError:
            return

        if isinstance(buttons, type) and issubclass(buttons, ButtonBuilder):
            buttons = [buttons]
        elif not isinstance(buttons, list):
            raise TypeError('Plugin.buttons must return a `ButtonBuilder` type or a list of `ButtonBuilder` types.')

        for i in buttons:
            if not isinstance(i, type) or not issubclass(i, ButtonBuilder):
                raise TypeError('Plugin.buttons must return a `ButtonBuilder` type or a list of `ButtonBuilder` types.')

            self.hub.telegram.ui_registry.add_button_builder(i)

    async def _run_setup_buttons_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.setup_buttons)

    async def _apply_button_modifications(self, plugin: LoadedPlugin) -> None:
        try:
            modifications = await plugin.plugin.button_modifications()
        except NotImplementedError:
            return

        for button_id, modifications_list in modifications.items():
            for i in modifications_list:
                self.hub.telegram.ui_registry.add_button_modification(i, button_id)

    async def _run_setup_button_modifications_step(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.setup_button_modifications)

    async def _run_post_setup(self, plugin: LoadedPlugin) -> None:
        await self._run_general_step(plugin.plugin.post_setup)

    async def _run_general_step(self, step: Callable[[], Awaitable[Any]]):
        with suppress(NotImplementedError):
            await step()

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    @property
    def plugins(self) -> MappingProxyType[str, LoadedPlugin]:
        return MappingProxyType(self._plugins)

    @property
    def disabled_plugins(self) -> frozenset[str]:
        return frozenset(self._disabled_plugins)
