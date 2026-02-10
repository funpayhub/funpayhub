from __future__ import annotations


__all__ = ['PluginManager', 'RepositoriesManager']

import sys
import json
import asyncio
import keyword
import importlib
from typing import Any
from copy import copy
from types import MappingProxyType
from pathlib import Path
from collections.abc import Callable, Awaitable

from pydantic import ValidationError
from packaging.version import Version

from loggers import plugins as logger

from funpayhub.lib.exceptions import (
    SaveRepositoryError,
    RemoveRepositoryError,
    TranslatableException,
    PluginInstantiationError,
    InvalidPluginRepositoryError,
    PluginRepositoryAlreadyExist,
)

from .types import LoadedPlugin, PluginManifest, PluginsRepository
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
            logger.info('Adding %s to sys.path.', str(self._plugins_path))
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
        logger.info('Loading plugins...')
        for i in self._plugins_path.iterdir():
            logger.debug('Checking %s...', str(i))
            if not i.is_dir():
                logger.debug('Ignoring %s: not a directory.', str(i))
                continue
            self.load_plugin(i)

    def load_plugin(self, plugin_path: str | Path, instantiate: bool = True) -> None:
        logger.info('Loading plugin %s...', str(plugin_path))

        module_name = Path(plugin_path).name
        if not module_name.isidentifier() or keyword.iskeyword(module_name):
            logger.warning('Ignoring %s: not a valid plugin directory.', str(plugin_path))
            return

        logger.info('Loading plugin manifest from %s.', str(plugin_path))
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
            logger.warning('Plugin %s already loaded. Skipping.', manifest.plugin_id)
            return

        exception: PluginInstantiationError | None = None

        if not instantiate:
            exception = PluginInstantiationError('Instantiation for this plugin disabled.')
        if self._safe_mode:
            exception = PluginInstantiationError('Safe mode enabled.')
        elif self._app_version not in manifest.app_version:
            exception = PluginInstantiationError(
                'App version mismatch. Plugin requires: %s. Current: %s.',
                manifest.app_version,
                self._app_version,
            )
        elif not self.is_enabled(manifest.plugin_id):
            exception = PluginInstantiationError('Plugin disabled.', manifest.plugin_id)

        plugin_instance = None
        if exception is not None:
            logger.error(exception.message, *exception.args)

        else:
            logger.info('Loading entry point %s of %s.', manifest.entry_point, manifest.plugin_id)
            try:
                plugin_instance = self._load_entry_point(plugin_path, manifest)
            except Exception as e:
                if isinstance(e, PluginInstantiationError):
                    logger.error(e.message, *e.args)
                    exception = e
                else:
                    logger.error(
                        'An error occurred while loading entry point %s of %s.',
                        manifest.entry_point,
                        manifest.plugin_id,
                        exc_info=True,
                    )
                    exception = PluginInstantiationError(
                        'An unexpected error occurred while instantiating plugin %s. See logs.',
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

    async def install_plugin_from_source(
        self,
        installer_class: type[PluginInstaller],
        source: Any,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> None:
        async with self.installation_lock:
            installer = installer_class(self._plugins_path, source, *args, **kwargs)
            path_to_plugin = await installer.install_wrapped(overwrite=overwrite)
            self.load_plugin(path_to_plugin, instantiate=False)

    def _load_plugin_manifest(self, plugin_path: str | Path) -> PluginManifest:
        with open(plugin_path / 'manifest.json', 'r', encoding='utf-8') as f:
            return PluginManifest.model_validate(json.loads(f.read()))

    async def setup_plugins(self) -> None:
        for step_name in self.steps_order:
            step = self._steps.get(step_name)
            if step is None:
                logger.warning('Step %s is not in plugin manager. Skipping.', step_name)
                continue

            for plugin_id, plugin in self._plugins.items():
                if not plugin.plugin:
                    logger.debug(
                        'Plugin %s does not have a plugin instance. Skipping step %s.',
                        plugin.manifest.plugin_id,
                        step_name,
                    )
                    continue
                logger.info('Running %s step for plugin %s.', step_name, plugin.manifest.plugin_id)
                await step(plugin)

    def _load_entry_point(self, plugin_path: str | Path, manifest: PluginManifest) -> PluginCLS:
        plugin_module_name = Path(plugin_path).name
        module_name, class_name = manifest.entry_point.rsplit('.', 1)

        module = importlib.import_module(f'{plugin_module_name}.{module_name}')
        plugin_class: type[PluginCLS] | None = getattr(module, class_name, None)

        if plugin_class is None:
            raise PluginInstantiationError(
                'Unable to find entry point %s of %s.',
                manifest.entry_point,
                manifest.plugin_id,
            )

        if not issubclass(plugin_class, self._plugin_cls):
            raise PluginInstantiationError(
                'Entry point of plugin must be a subclass of %s, not %s.',
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


class RepositoriesManager:
    def __init__(self, repositories_path: str | Path) -> None:
        self._repositories_path = Path(repositories_path)
        self._repositories: dict[str, PluginsRepository] = {}
        self._load_repositories()

    def load_repository(
        self,
        repository: dict[str, Any],
        register: bool = True,
        save: bool = False,
    ) -> PluginsRepository:
        if not isinstance(repository, PluginsRepository):
            try:
                repository = PluginsRepository.model_validate(repository)
            except ValidationError as e:
                raise InvalidPluginRepositoryError() from e

        if save:
            if repository.id in self._repositories:
                raise PluginRepositoryAlreadyExist(repository.id)
            self.save_repository(repository)

        if register:
            self.register_repository(repository)

        return repository

    def register_repository(self, repository: PluginsRepository) -> None:
        if repository.id in self._repositories:
            raise PluginRepositoryAlreadyExist(repository.id)
        self._repositories[repository.id] = repository

    def _save_repository(self, repository: PluginsRepository, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as f:
            f.write(repository.to_json())

    def _load_repositories(self) -> None:
        logger.info('Loading plugins repositories from %s...', str(self._repositories_path))
        if not self._repositories_path.exists():
            return
        if self._repositories_path.is_file():
            return

        for i in self._repositories_path.iterdir():
            if i.is_dir():
                logger.debug('%s is a directory. Skipping.', str(i))
                continue
            if not i.suffix == '.json':
                logger.warning('%s is not a JSON file. Skipping.', str(i))
                continue

            logger.info('Loading plugins repository from %s...', str(i))
            try:
                with i.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    repo = self.load_repository(data, save=False, register=False)
                    if repo.id != i.stem:
                        logger.warning(
                            'Repository ID %s does not match repo file %s. Skipping.',
                            repo.id,
                            i.name,
                        )
                        continue
                    self.register_repository(repo)
            except Exception as e:
                if isinstance(e, TranslatableException):
                    logger.error(e.message, *e.args, exc_info=True)
                else:
                    logger.error(
                        'An error occurred while loading plugin repository from %s.',
                        str(i),
                        exc_info=True,
                    )

    def save_repository(self, repository: PluginsRepository) -> None:
        save_path = self._repository_file_path(repository.id)
        try:
            self._save_repository(repository, save_path)
        except:
            raise SaveRepositoryError(repository.id, save_path)

    def remove_repository(self, repository_id: str) -> None:
        if repository_id not in self._repositories:
            return

        repository_path = self._repository_file_path(repository_id)
        if repository_path.exists() and repository_path.is_file():
            try:
                repository_path.unlink()
            except:
                raise RemoveRepositoryError(repository_id, repository_path)

        self._repositories.pop(repository_id, None)

    def _repository_file_path(self, repository_id: str) -> Path:
        return self._repositories_path / (repository_id + '.json')

    @property
    def repositories(self) -> dict[str, PluginsRepository]:
        return copy(self._repositories)
