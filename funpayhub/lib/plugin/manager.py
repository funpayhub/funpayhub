from __future__ import annotations

from funpayhub.lib.translater import _en


__all__ = ['PluginManager']

import sys
import json
import asyncio
import keyword
import importlib
from typing import Any
from types import MappingProxyType
from pathlib import Path
from collections.abc import Callable, Awaitable

from packaging.version import Version

from loggers import plugins as logger

from funpayhub.lib.exceptions import (
    PluginInstantiationError,
)

from .types import LoadedPlugin, PluginManifest
from .installers import PluginInstaller


type RESOLVABLE = LoadedPlugin | PluginManifest | str
type STEP = Callable[[LoadedPlugin], Awaitable[Any]]
type INIT_ARGS_FACTORY = Callable[[PluginManifest], tuple[Any, ...]]


def _resolve_plugin_id(_v: RESOLVABLE) -> str:
    if isinstance(_v, str):
        return _v
    if isinstance(_v, PluginManifest):
        return _v.plugin_id
    if isinstance(_v, LoadedPlugin):
        return _v.manifest.plugin_id

    raise TypeError(f'Unable to resolve plugin ID for {_v!r}')


class PluginManager[PluginCLS]:
    def __init__(
        self,
        plugins_path: Path,
        app_version: Version,
        plugin_cls: type[PluginCLS],
        init_args_factory: INIT_ARGS_FACTORY,
        safe_mode: bool = False,
    ) -> None:
        self._plugins_path = plugins_path
        self._safe_mode = safe_mode
        self._app_version = app_version

        self._plugin_cls = plugin_cls
        self._init_args_factory = init_args_factory

        self._plugins: dict[str, LoadedPlugin] = {}
        self._steps: dict[str, STEP] = {}
        self.steps_order: list[str] = []
        self._disabled_plugins: set[str] = set()

        if self._plugins_path not in sys.path:
            logger.info(_en('Adding %s to sys.path.'), str(self._plugins_path))
            sys.path.append(str(self._plugins_path))

        self._installation_lock = asyncio.Lock()

    def add_step(self, step_name: str, step: STEP) -> None:
        if step_name in self._steps:
            raise ValueError(f'Step {step_name} already registered.')
        self._steps[step_name] = step
        self.steps_order.append(step_name)

    def set_order(self, steps_order: list[str]) -> None:
        self.steps_order = steps_order

    async def disable_plugin(self, plugin: RESOLVABLE) -> None:
        plugin_id = _resolve_plugin_id(plugin)
        if not plugin_id:
            return

        self._disabled_plugins.add(plugin_id)

    async def enable_plugin(self, plugin: RESOLVABLE) -> None:
        plugin_id = _resolve_plugin_id(plugin)
        if not plugin_id:
            return

        self._disabled_plugins.discard(plugin_id)

    def is_enabled(self, plugin: RESOLVABLE) -> bool:
        plugin = _resolve_plugin_id(plugin)
        return plugin not in self.disabled_plugins

    async def load_plugins(self) -> None:
        logger.info(_en('Loading plugins...'))
        if not self._plugins_path.exists():
            logger.info(_en('%s does not exists. Skipping.'), str(self._plugins_path))
            return

        for i in self._plugins_path.iterdir():
            logger.debug(_en('Checking %s...'), str(i))
            if not i.is_dir():
                logger.debug(_en('Ignoring %s: not a directory.'), str(i))
                continue
            self.load_plugin(i)

    def load_plugin(
        self,
        plugin_path: str | Path,
        instantiate: bool = True,
    ) -> LoadedPlugin | None:
        logger.info(_en('Loading plugin %s...'), str(plugin_path))

        module_name = Path(plugin_path).name
        if not module_name.isidentifier() or keyword.iskeyword(module_name):
            logger.warning(_en('Ignoring %s: not a valid plugin directory.'), str(plugin_path))
            return None

        logger.info(_en('Loading plugin manifest from %s.'), str(plugin_path))
        try:
            manifest = self._load_plugin_manifest(plugin_path)
        except:
            logger.error(
                _en('Unable to load plugin manifest for %s. Skipping.'),
                str(plugin_path),
                exc_info=True,
            )
            return None

        if manifest.plugin_id in self._plugins:
            logger.warning(_en('Plugin %s already loaded. Skipping.'), manifest.plugin_id)
            return None

        exception: PluginInstantiationError | None = None

        if not instantiate:
            exception = PluginInstantiationError(_en('Instantiation for this plugin disabled.'))
        if self._safe_mode:
            exception = PluginInstantiationError('Safe mode enabled.')
        elif self._app_version not in manifest.app_version:
            exception = PluginInstantiationError(
                _en('App version mismatch. Plugin requires: %s. Current: %s.'),
                manifest.app_version,
                self._app_version,
            )
        elif not self.is_enabled(manifest.plugin_id):
            exception = PluginInstantiationError('Plugin disabled.', manifest.plugin_id)

        plugin_instance = None
        if exception is not None:
            logger.error(exception.message, *exception.args)

        else:
            logger.info(
                _en('Loading entry point %s of %s.'),
                manifest.entry_point,
                manifest.plugin_id,
            )
            try:
                plugin_instance = self._load_entry_point(plugin_path, manifest)
            except Exception as e:
                if isinstance(e, PluginInstantiationError):
                    logger.error(e.message, *e.args)
                    exception = e
                else:
                    logger.error(
                        _en('An error occurred while loading entry point %s of %s.'),
                        manifest.entry_point,
                        manifest.plugin_id,
                        exc_info=True,
                    )
                    exception = PluginInstantiationError(
                        _en(
                            'An unexpected error occurred while instantiating plugin %s. See logs.',
                        ),
                        manifest.plugin_id,
                    )
                    exception.__cause__ = e

        plugin = LoadedPlugin(
            path=Path(plugin_path),
            manifest=manifest,
            plugin=plugin_instance,
            error=exception,
        )
        self._plugins[manifest.plugin_id] = plugin
        return plugin

    async def install_plugin_from_source(
        self,
        installer_class: type[PluginInstaller],
        source: Any,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> LoadedPlugin | None:
        async with self.installation_lock:
            installer = installer_class(self._plugins_path, source, *args, **kwargs)
            path_to_plugin = await installer.install_wrapped(overwrite=overwrite)
            return self.load_plugin(path_to_plugin, instantiate=False)

    def _load_plugin_manifest(self, plugin_path: str | Path) -> PluginManifest:
        with open(plugin_path / 'manifest.json', 'r', encoding='utf-8') as f:
            return PluginManifest.model_validate(json.loads(f.read()))

    async def setup_plugins(self) -> None:
        for step_name in self.steps_order:
            step = self._steps.get(step_name)
            if step is None:
                logger.warning(_en('Step %s is not in plugin manager. Skipping.'), step_name)
                continue

            for plugin_id, plugin in self._plugins.items():
                if not plugin.plugin:
                    logger.debug(
                        _en('Plugin %s does not have a plugin instance. Skipping step %s.'),
                        plugin.manifest.plugin_id,
                        step_name,
                    )
                    continue
                logger.info(
                    _en('Running %s step for plugin %s.'),
                    step_name,
                    plugin.manifest.plugin_id,
                )
                await step(plugin)

    def _load_entry_point(self, plugin_path: str | Path, manifest: PluginManifest) -> PluginCLS:
        plugin_module_name = Path(plugin_path).name
        module_name, class_name = manifest.entry_point.rsplit('.', 1)

        module = importlib.import_module(f'{plugin_module_name}.{module_name}')
        plugin_class: type[PluginCLS] | None = getattr(module, class_name, None)

        if plugin_class is None:
            raise PluginInstantiationError(
                _en('Unable to find entry point %s of %s.'),
                manifest.entry_point,
                manifest.plugin_id,
            )

        if not issubclass(plugin_class, self._plugin_cls):
            raise PluginInstantiationError(
                _en('Entry point of plugin must be a subclass of %s, not %s.'),
                self._plugin_cls.__name__,
                plugin_class.__name__,
            )

        return plugin_class(*self._init_args_factory(manifest))

    @property
    def plugins(self) -> MappingProxyType[str, LoadedPlugin]:
        return MappingProxyType(self._plugins)

    @property
    def disabled_plugins(self) -> frozenset[str]:
        return frozenset(self._disabled_plugins)

    @property
    def installation_lock(self) -> asyncio.Lock:
        return self._installation_lock

    @property
    def plugins_path(self) -> Path:
        return self._plugins_path

    @property
    def steps(self) -> MappingProxyType[str, STEP]:
        return MappingProxyType(self._steps)
