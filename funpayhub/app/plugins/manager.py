from __future__ import annotations
from typing import TYPE_CHECKING, Any
from funpayhub.lib.plugins import PluginManager as BasePluginManager
import os
from pathlib import Path
from .plugin import Plugin
from aiogram import BaseMiddleware
from eventry.asyncio.middleware_manager import MiddlewareManagerTypes
from contextlib import suppress

if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.lib.plugins import PluginManifest, LoadedPlugin
    from aiogram import Router as AiogramRouter
    from eventry.asyncio.router import Router as EventryRouter
    from funpaybotengine import Router as FPBERouter
    from funpayhub.app.dispatching import Router as HubRouter
    from collections.abc import Callable, Awaitable


class PassPluginAiogramMiddleware(BaseMiddleware):
    def __init__(self, plugin: LoadedPlugin[Plugin]) -> None:
        self.plugin = plugin

    async def __call__(self, handler: Any, event: Any, data: dict[str, Any]) -> Any:
        data['plugin'] = self.plugin
        data['plugin_properties'] = self.plugin.properties
        data['plugin_manifest'] = self.plugin.manifest
        return await handler(event, data)


class PassPluginEventryMiddleware:
    def __init__(self, plugin: LoadedPlugin[Plugin]) -> None:
        self.plugin = plugin

    async def __call__(self, data: dict[str, Any]) -> Any:
        data['plugin'] = self.plugin
        data['plugin_properties'] = self.plugin.properties
        data['plugin_manifest'] = self.plugin.manifest
        return


def setup_aiogram_router(plugin: LoadedPlugin[Plugin], *routers: AiogramRouter) -> AiogramRouter:
    wrapper_router = AiogramRouter(name=f'plugin_wrapper:{plugin.manifest.plugin_id}')
    middleware = PassPluginAiogramMiddleware(plugin)
    for i in wrapper_router.observers.values():
        i.outer_middleware(middleware)

    wrapper_router.include_routers(*routers)
    return wrapper_router


def setup_eventry_plugin_router(router: EventryRouter, plugin: LoadedPlugin[Plugin]) -> None:
    middleware = PassPluginEventryMiddleware(plugin)
    for i in router._handler_managers.values():
        manager = i.middleware_manager(MiddlewareManagerTypes.MANAGER_OUTER)
        if manager is None:
            continue
        manager.register_middleware(middleware)


def setup_hub_router(plugin: LoadedPlugin[Plugin], *routers: HubRouter) -> HubRouter:
    wrapper_router = HubRouter(f'plugin_wrapper:{plugin.manifest.plugin_id}')
    setup_eventry_plugin_router(wrapper_router, plugin)
    wrapper_router.connect_routers(*routers)
    return wrapper_router


def setup_botengine_router(plugin: LoadedPlugin[Plugin], *routers: FPBERouter) -> FPBERouter:
    wrapper_router = FPBERouter(f'plugin_wrapper:{plugin.manifest.plugin_id}')
    setup_eventry_plugin_router(wrapper_router, plugin)
    wrapper_router.connect_routers(*routers)
    return wrapper_router


class PluginManager(BasePluginManager[Plugin]):
    def __init__(self, hub: FunPayHub, safe_mode: bool = False):
        super().__init__(
            plugins_path=Path(os.getcwd()) / 'plugins',
            app_version=hub.properties.version,
            plugin_cls=Plugin,
            init_args_factory=self.args_factory,
            safe_mode=safe_mode
        )

        self._hub = hub

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
            'apply_commands': self._apply_commands,
            'setup_commands': self._setup_commands,
            'apply_formatters': self._apply_formatters,
            'setup_formatters': self._setup_formatters,
            'post_setup': self._run_post_setup,
        }

        for step_name, step in steps.items():
            self.add_step(step_name, step)

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    def args_factory(self, manifest: PluginManifest) -> tuple[Any, ...]:
        return manifest, self._hub

    async def _run_pre_setup_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.pre_setup)

    async def _apply_properties(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (properties := await self._run_step(plugin.plugin.properties)) is None:
            return

        self.hub.properties.plugin_properties.attach_node(properties)
        await self.hub.properties.load()
        self.plugins[plugin.manifest.plugin_id].properties = properties

    async def _run_setup_properties_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_properties)
        await self.hub.properties.load()

    async def _apply_hub_routers(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (routers := await self._run_step(plugin.plugin.hub_routers)) is None:
            return

        if not isinstance(routers, list):
            routers = [routers]

        self.hub.dispatcher.connect_router(setup_hub_router(plugin, *routers))

    async def _run_setup_hub_routers_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_hub_routers)

    async def _apply_funpay_routers(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (routers := await self._run_step(plugin.plugin.funpay_routers)) is None:
            return

        if not isinstance(routers, list):
            routers = [routers]

        self.hub.funpay.dispatcher.connect_router(setup_botengine_router(plugin, *routers))

    async def _run_setup_funpay_routers_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_funpay_routers)

    async def _apply_telegram_routers(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (routers := await self._run_step(plugin.plugin.telegram_routers)) is None:
            return

        if not isinstance(routers, list):
            routers = [routers]

        self.hub.telegram.dispatcher.include_router(setup_aiogram_router(plugin, *routers))

    async def _run_setup_telegram_routers_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_telegram_routers)

    async def _apply_menus(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (menus := await self._run_step(plugin.plugin.menus)) is None:
            return

        if not isinstance(menus, list):
            menus = [menus]

        for i in menus:
            self.hub.telegram.ui_registry.add_menu_builder(i)

    async def _run_setup_menus_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_menus)

    async def _apply_menu_modifications(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (modifications := await self._run_step(plugin.plugin.menu_modifications)) is None:
            return

        for menu_id, modifications_list in modifications.items():
            if not isinstance(modifications_list, list):
                modifications_list = [modifications_list]

            for i in modifications_list:
                self.hub.telegram.ui_registry.add_menu_modification(i, menu_id)

    async def _run_setup_menu_modifications_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_menu_modifications)

    async def _apply_buttons(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (buttons := await self._run_step(plugin.plugin.buttons)) is None:
            return

        if not isinstance(buttons, list):
            buttons = [buttons]

        for i in buttons:
            self.hub.telegram.ui_registry.add_button_builder(i)

    async def _run_setup_buttons_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_buttons)

    async def _apply_button_modifications(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (modifications := await self._run_step(plugin.plugin.button_modifications)) is None:
            return

        for button_id, modifications_list in modifications.items():
            if not isinstance(modifications_list, list):
                modifications_list = [modifications_list]
            for i in modifications_list:
                self.hub.telegram.ui_registry.add_button_modification(i, button_id)

    async def _run_setup_button_modifications_step(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_button_modifications)

    async def _apply_commands(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (result := await self._run_step(plugin.plugin.commands)) is None:
            return

        if not isinstance(result, list):
            result = [result]

        for i in result:
            self.hub.telegram._commands.add_command(i)

    async def _setup_commands(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_commands)

    async def _apply_formatters(self, plugin: LoadedPlugin[Plugin]) -> None:
        if (result := await self._run_step(plugin.plugin.formatters)) is None:
            return

        if not isinstance(result, list):
            result = [result]

        for i in result:
            self.hub.funpay.text_formatters.add_formatter(i)

    async def _setup_formatters(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.setup_formatters)

    async def _run_post_setup(self, plugin: LoadedPlugin[Plugin]) -> None:
        await self._run_step(plugin.plugin.post_setup)

    async def _run_step[R: Any](self, step: Callable[[], Awaitable[R]]) -> R | None:
        with suppress(NotImplementedError):
            return await step()
        return None