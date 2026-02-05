from __future__ import annotations
from typing import TYPE_CHECKING, Any
from funpayhub.lib.plugins import PluginManager as BasePluginManager
import os
from pathlib import Path
from .plugin import Plugin
from aiogram import BaseMiddleware
from eventry.asyncio.middleware_manager import MiddlewareManagerTypes

if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.lib.plugins import PluginManifest, LoadedPlugin
    from aiogram import Router as AiogramRouter
    from eventry.asyncio.router import Router as EventryRouter
    from funpaybotengine import Router as FPBERouter
    from funpayhub.app.dispatching import Router as HubRouter


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


class PluginManager(BasePluginManager):
    def __init__(self, hub: FunPayHub, safe_mode: bool = False):
        super().__init__(
            plugins_path=Path(os.getcwd()) / 'plugins',
            app_version=hub.properties.version,
            plugin_cls=Plugin,
            init_args_factory=self.args_factory,
            safe_mode=safe_mode
        )

        self._hub = hub

    def args_factory(self, manifest: PluginManifest) -> tuple[Any, ...]:
        return manifest, self._hub