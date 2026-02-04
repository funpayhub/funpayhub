from __future__ import annotations


__all__ = ['PluginManager']

import os
import sys
import json
import asyncio
import keyword
import importlib
from typing import TYPE_CHECKING, Any
from types import MappingProxyType
from pathlib import Path
from itertools import chain
from contextlib import suppress
from collections.abc import Callable, Awaitable

from aiogram import Router as AiogramRouter, BaseMiddleware
from funpaybotengine import Router as FPBERouter
from packaging.version import Version
from eventry.asyncio.router import Router as EventryRouter
from eventry.asyncio.middleware_manager import MiddlewareManagerTypes

from loggers import plugins as logger
from funpayhub.app.dispatching import Router as HubRouter

from .types import Plugin, LoadedPlugin, PluginManifest
from .installers import PluginInstaller


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub  # todo: lib depends from app :(


type RESOLVABLE = Plugin | LoadedPlugin | PluginManifest | str


def _resolve_plugin_id(_v: RESOLVABLE) -> str:
    if isinstance(_v, str):
        return _v
    if isinstance(_v, (Plugin, LoadedPlugin)):
        return _v.manifest.plugin_id
    if isinstance(_v, PluginManifest):
        return _v.plugin_id

    raise TypeError(f'Unable to resolve plugin ID for {_v!r}')


class PassPluginAiogramMiddleware(BaseMiddleware):
    def __init__(self, plugin: LoadedPlugin) -> None:
        self.plugin = plugin

    async def __call__(self, handler: Any, event: Any, data: dict[str, Any]) -> Any:
        data['plugin'] = self.plugin
        data['plugin_properties'] = self.plugin.properties
        data['plugin_manifest'] = self.plugin.manifest
        return await handler(event, data)


class PassPluginEventryMiddleware:
    def __init__(self, plugin: LoadedPlugin) -> None:
        self.plugin = plugin

    async def __call__(self, data: dict[str, Any]) -> Any:
        data['plugin'] = self.plugin
        data['plugin_properties'] = self.plugin.properties
        data['plugin_manifest'] = self.plugin.manifest
        return


def setup_aiogram_router(plugin: LoadedPlugin, *routers: AiogramRouter) -> AiogramRouter:
    wrapper_router = AiogramRouter(name=f'plugin_wrapper:{plugin.manifest.plugin_id}')
    middleware = PassPluginAiogramMiddleware(plugin)
    for i in wrapper_router.observers.values():
        i.outer_middleware(middleware)

    wrapper_router.include_routers(*routers)
    return wrapper_router


def setup_eventry_plugin_router(router: EventryRouter, plugin: LoadedPlugin) -> None:
    middleware = PassPluginEventryMiddleware(plugin)
    for i in router._handler_managers.values():
        manager = i.middleware_manager(MiddlewareManagerTypes.MANAGER_OUTER)
        if manager is None:
            continue
        manager.register_middleware(middleware)


def setup_hub_router(plugin: LoadedPlugin, *routers: HubRouter) -> HubRouter:
    wrapper_router = HubRouter(f'plugin_wrapper:{plugin.manifest.plugin_id}')
    setup_eventry_plugin_router(wrapper_router, plugin)
    wrapper_router.connect_routers(*routers)
    return wrapper_router


def setup_botengine_router(plugin: LoadedPlugin, *routers: FPBERouter) -> FPBERouter:
    wrapper_router = FPBERouter(f'plugin_wrapper:{plugin.manifest.plugin_id}')
    setup_eventry_plugin_router(wrapper_router, plugin)
    wrapper_router.connect_routers(*routers)
    return wrapper_router


class PluginManager:
    PLUGINS_PATH = Path(os.getcwd()) / 'plugins'

    def __init__(self, hub: FunPayHub) -> None:
        self._plugins: dict[str, LoadedPlugin] = {}
        self._hub = hub
        self._steps: dict[str, Callable[[LoadedPlugin], Awaitable[Any]]] = {
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
            'apply_commands': self._apply_commands,
            'setup_commands': self._setup_commands,
            'apply_formatters': self._apply_formatters,
            'setup_formatters': self._setup_formatters,
            'post_setup': self._run_post_setup,
        }

        if self.PLUGINS_PATH not in sys.path:
            logger.info('Adding %s to %s.', str(self.PLUGINS_PATH), 'sys.path')
            sys.path.append(str(self.PLUGINS_PATH))

        self._installation_lock = asyncio.Lock()

    @property
    def installation_lock(self) -> asyncio.Lock:
        return self._installation_lock

    async def disable_plugin(self, plugin: RESOLVABLE) -> None:
        plugin = _resolve_plugin_id(plugin)
        if not plugin:
            return

        if self.is_enabled(plugin):
            await self.hub.properties.plugin_properties.disabled_plugins.add_item(plugin)

    async def enable_plugin(self, plugin: RESOLVABLE) -> None:
        plugin = _resolve_plugin_id(plugin)
        if not plugin:
            return

        if not self.is_enabled(plugin):
            await self.hub.properties.plugin_properties.disabled_plugins.remove_item(plugin)

    def is_enabled(self, plugin: RESOLVABLE) -> bool:
        plugin = _resolve_plugin_id(plugin)
        return plugin not in self.disabled_plugins

    async def load_plugins(self) -> None:
        for i in self.PLUGINS_PATH.iterdir():
            if not i.is_dir():
                logger.debug('Ignoring %s: not a directory.', str(i))
                continue
            self.load_plugin(i)

    def load_plugin(self, plugin_path: str | Path, instantiate: bool = True) -> None:
        logger.info('Loading plugin %s.', str(plugin_path))

        module_name = Path(plugin_path).name
        if not module_name.isidentifier() or keyword.iskeyword(module_name):
            logger.warning('Ignoring %s: not a valid plugin directory.', str(plugin_path))
            return

        logger.info('Loading manifest for %s.', str(plugin_path))
        try:
            manifest = self._load_plugin_manifest(plugin_path)
        except:
            logger.error(
                'Unable to load plugin manifest for %s. Skipping.',
                str(plugin_path),
                exc_info=True,
            )
            return

        if manifest.plugin_id in self._plugins:
            logger.warning('Plugin %s is already loaded. Skipping.', manifest.plugin_id)
            return

        if Version(self.hub.properties.version.value) not in manifest.hub_version:
            raise RuntimeError(
                'FunPay Hub version mismatch. Expected: %s. Current: %s.'
                % (manifest.hub_version, self.hub.properties.version.value),
            )

        plugin_instance = None
        if not self.is_enabled(manifest.plugin_id):
            logger.info('Plugin %s is disabled. Skipping.', manifest.plugin_id)
        elif instantiate:
            logger.info('Loading entry point %s of %s.', manifest.entry_point, manifest.plugin_id)
            plugin_instance = self._load_entry_point(plugin_path, manifest)

        plugin = LoadedPlugin(
            path=Path(plugin_path),
            manifest=manifest,
            plugin=plugin_instance,
        )
        self._plugins[manifest.plugin_id] = plugin

    async def install_plugin_from_source(
        self,
        installer_class: type[PluginInstaller],
        source: Any,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> None:
        async with self.installation_lock:
            installer = installer_class(self.PLUGINS_PATH, source, *args, **kwargs)
            path_to_plugin = await installer.install_wrapped(overwrite=overwrite)
            self.load_plugin(path_to_plugin, instantiate=False)

    def _load_plugin_manifest(self, plugin_path: str | Path) -> PluginManifest:
        with open(plugin_path / 'manifest.json', 'r', encoding='utf-8') as f:
            return PluginManifest.model_validate(json.loads(f.read()))

    async def setup_plugins(self) -> None:
        for plugin_id, plugin in self._plugins.items():
            if not plugin.manifest.locales_path:
                logger.info(
                    'Plugin %s does not have a locales path. Skipping locales installation.',
                    plugin_id,
                )
                continue

            try:
                logger.info('Loading locales for plugin %s.', plugin_id)
                locales_path = Path(plugin.manifest.locales_path)
                real_path = plugin.path / locales_path
                self.hub.translater.add_translations(real_path)
            except Exception:
                logger.warning(
                    'Unable to load locales for plugin %s. '
                    'This will not stop plugin from setting up.',
                    plugin_id,
                    exc_info=True,
                )

        for name, step in self._steps.items():
            for plugin_id, plugin in self._plugins.items():
                if not plugin.plugin:
                    logger.info(
                        'Plugin %s does not have a plugin instance. Skipping step %s.',
                        plugin.manifest.plugin_id,
                        name,
                    )
                    continue
                logger.info('Running %s step for plugin %s.', name, plugin.manifest.plugin_id)
                await step(plugin)

    def _load_entry_point(
        self,
        plugin_path: str | Path,
        manifest: PluginManifest,
    ) -> Plugin:
        plugin_module_name = Path(plugin_path).name
        module_name, class_name = manifest.entry_point.rsplit('.', 1)

        module = importlib.import_module(f'{plugin_module_name}.{module_name}')
        plugin_class: type[Plugin] | None = getattr(module, class_name, None)

        if plugin_class is None:
            raise RuntimeError(f'Unable to find {plugin_path} at {manifest}.')

        if not issubclass(plugin_class, Plugin):
            raise TypeError('Entry point must be a subclass of Plugin.')

        return plugin_class(manifest, self._hub)

    async def _run_pre_setup_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.pre_setup)

    async def _apply_properties(self, plugin: LoadedPlugin) -> None:
        if (properties := await self._run_step(plugin.plugin.properties)) is None:
            return

        self.hub.properties.plugin_properties.attach_node(properties)
        await self.hub.properties.load()
        self.plugins[plugin.manifest.plugin_id].properties = properties

    async def _run_setup_properties_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_properties)
        await self.hub.properties.load()

    async def _apply_hub_routers(self, plugin: LoadedPlugin) -> None:
        if (routers := await self._run_step(plugin.plugin.hub_routers)) is None:
            return

        if not isinstance(routers, list):
            routers = [routers]

        self.hub.dispatcher.connect_router(setup_hub_router(plugin, *routers))

    async def _run_setup_hub_routers_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_hub_routers)

    async def _apply_funpay_routers(self, plugin: LoadedPlugin) -> None:
        if (routers := await self._run_step(plugin.plugin.funpay_routers)) is None:
            return

        if not isinstance(routers, list):
            routers = [routers]

        self.hub.funpay.dispatcher.connect_router(setup_botengine_router(plugin, *routers))

    async def _run_setup_funpay_routers_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_funpay_routers)

    async def _apply_telegram_routers(self, plugin: LoadedPlugin) -> None:
        if (routers := await self._run_step(plugin.plugin.telegram_routers)) is None:
            return

        if not isinstance(routers, list):
            routers = [routers]

        self.hub.telegram.dispatcher.include_router(setup_aiogram_router(plugin, *routers))

    async def _run_setup_telegram_routers_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_telegram_routers)

    async def _apply_menus(self, plugin: LoadedPlugin) -> None:
        if (menus := await self._run_step(plugin.plugin.menus)) is None:
            return

        if not isinstance(menus, list):
            menus = [menus]

        for i in menus:
            self.hub.telegram.ui_registry.add_menu_builder(i)

    async def _run_setup_menus_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_menus)

    async def _apply_menu_modifications(self, plugin: LoadedPlugin) -> None:
        if (modifications := await self._run_step(plugin.plugin.menu_modifications)) is None:
            return

        for menu_id, modifications_list in modifications.items():
            if not isinstance(modifications_list, list):
                modifications_list = [modifications_list]

            for i in modifications_list:
                self.hub.telegram.ui_registry.add_menu_modification(i, menu_id)

    async def _run_setup_menu_modifications_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_menu_modifications)

    async def _apply_buttons(self, plugin: LoadedPlugin) -> None:
        if (buttons := await self._run_step(plugin.plugin.buttons)) is None:
            return

        if not isinstance(buttons, list):
            buttons = [buttons]

        for i in buttons:
            self.hub.telegram.ui_registry.add_button_builder(i)

    async def _run_setup_buttons_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_buttons)

    async def _apply_button_modifications(self, plugin: LoadedPlugin) -> None:
        if (modifications := await self._run_step(plugin.plugin.button_modifications)) is None:
            return

        for button_id, modifications_list in modifications.items():
            if not isinstance(modifications_list, list):
                modifications_list = [modifications_list]
            for i in modifications_list:
                self.hub.telegram.ui_registry.add_button_modification(i, button_id)

    async def _run_setup_button_modifications_step(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_button_modifications)

    async def _apply_commands(self, plugin: LoadedPlugin) -> None:
        if (result := await self._run_step(plugin.plugin.commands)) is None:
            return

        if not isinstance(result, list):
            result = [result]

        for i in result:
            self.hub.telegram._commands.add_command(i)

    async def _setup_commands(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_commands)

    async def _apply_formatters(self, plugin: LoadedPlugin) -> None:
        if (result := await self._run_step(plugin.plugin.formatters)) is None:
            return

        if not isinstance(result, list):
            result = [result]

        for i in result:
            self.hub.funpay.text_formatters.add_formatter(i)

    async def _setup_formatters(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.setup_formatters)

    async def _run_post_setup(self, plugin: LoadedPlugin) -> None:
        await self._run_step(plugin.plugin.post_setup)

    async def _run_step[R: Any](self, step: Callable[[], Awaitable[R]]) -> R | None:
        with suppress(NotImplementedError):
            return await step()
        return None

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    @property
    def plugins(self) -> MappingProxyType[str, LoadedPlugin]:
        return MappingProxyType(self._plugins)

    @property
    def disabled_plugins(self) -> frozenset[str]:
        return frozenset(self.hub.properties.plugin_properties.disabled_plugins.value)
