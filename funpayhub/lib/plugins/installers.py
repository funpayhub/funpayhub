from __future__ import annotations

import os
import shutil
from typing import Any
from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from aiogram import Bot
from aiohttp import ClientSession

from loggers import plugins as logger


class PluginInstallationError(Exception):
    def __init__(self, message: str, *args):
        super().__init__(message, *args)

    def __str__(self) -> str:
        return self.args[0] % self.args[1:]


class PluginInstaller[T: Any](ABC):
    """
    Базовый установщик плагинов.

    Установщик плагинов скачивает (если требуется) и копирует файлы плагина в директорию плагинов,
    после чего возвращает путь до установленного плагина, после чего менеджер загружает его
    манифест.

    Если установка невозможна или завершилась ошибкой, установщик должен возбудить
    `PluginInstallationError`.

    Каждый установщик должен при инициализации принимать путь до директории с плагинами,
    куда необходимо установить плагин и ссылку на ресурс.
    Ссылкой на ресурс может быть что угодно, будь то путь до ZIP архива, URL адресом,
    git-репозиторием и т.п., каждая реализация должна сама проверять, подходит ли ей
    переданный `source`.
    """

    def __init__(self, plugins_directory: Path, source: T, *args: Any, **kwargs: Any) -> None:
        self._plugins_directory = plugins_directory
        self._source = source

    @property
    def plugins_directory(self) -> Path:
        return self._plugins_directory

    @property
    def source(self) -> T:
        return self._source

    @abstractmethod
    async def install(self, overwrite: bool = False) -> Path:
        pass

    async def install_wrapped(self, overwrite: bool = False) -> Path:
        logger.info('Installing plugin from source %s ...', self._source)
        try:
            return await self.install(overwrite=overwrite)
        except PluginInstallationError:
            logger.error('Failed to install plugin from source %s.', exc_info=True)
            raise
        except Exception as e:
            logger.error('Failed to install plugin from source %s.', exc_info=True)
            raise PluginInstallationError('Unable to install plugin. See logs.') from e


class ZipPluginInstaller(PluginInstaller[str | Path]):
    """
    Установщик плагинов из ZIP-архивов.

    ZIP-архив обязан содержать ровно одну запись в корне — директорию плагина.
    Все файлы и поддиректории плагина должны находиться внутри неё.

    Имя корневой директории должно быть валидным Python-идентификатором (`str.isidentifier()`),
    поскольку в дальнейшем оно используется как: имя пакета, имя для импортов,
    часть публичного API плагина и т.д.

    Архивы с иной структурой считаются некорректными и установке не подлежат.
    """

    def __init__(self, plugins_path: Path, source: str | Path) -> None:
        if not isinstance(source, (str, Path)):
            raise ValueError('Source must be a string or a `pathlib.Path`.')

        source = Path(source)
        super().__init__(plugins_path, source)
        self._check_archive_exists()

    async def install(self, overwrite: bool = False) -> Path:
        self._check_archive_exists()
        with ZipFile(self.source) as zf:
            root = self._check_root(zf)
            if self._check_exists(root) and not overwrite:
                raise PluginInstallationError(
                    'Unable to install plugin: %s already exists.',
                    self.plugins_directory / root,
                )

            with Mover(self.plugins_directory / root):
                zf.extractall(self.plugins_directory)

        return self.plugins_directory / root

    def _check_exists(self, dir_name: str) -> bool:
        return self.plugins_directory.exists() and dir_name in os.listdir(self.plugins_directory)

    def _check_root(self, archive: ZipFile) -> str:
        root_name = None
        for i in archive.infolist():
            path = PurePosixPath(i.filename)
            if path.is_absolute():
                raise PluginInstallationError(
                    'Invalid archive structure: archive contains absolute path %s, '
                    'which is not allowed. All paths must be relative.',
                    path,
                )

            if len(path.parts) == 1 and not i.is_dir():
                raise PluginInstallationError(
                    'Invalid archive structure: the root of the ZIP must contain exactly '
                    'one directory, but found a file: %s',
                    i.filename,
                )

            curr_root_name = path.parts[0]

            if not curr_root_name.isidentifier():
                raise PluginInstallationError(
                    'Invalid archive structure: the root directory name %s '
                    'is not a valid Python identifier. It must be suitable for imports.',
                    curr_root_name,
                )

            if root_name is not None and curr_root_name != root_name:
                raise PluginInstallationError(
                    'Invalid archive structure: expected all entries to be under '
                    'root directory %s, but found entry %s outside of it.',
                    root_name,
                    path,
                )

            root_name = curr_root_name

        if root_name is None:
            raise PluginInstallationError(
                'Invalid archive structure: archive is empty.',
            )
        return root_name

    def _check_archive_exists(self) -> None:
        if not self.source.exists():
            raise FileNotFoundError(f'Source {self.source} does not exist.')
        if not self.source.is_file():
            raise ValueError(f'Source {self.source} is not a file.')


class HTTPSPluginInstaller(PluginInstaller[str]):
    def __init__(
        self,
        plugins_path: Path,
        source: str,
        installer_class: type[PluginInstaller] = ZipPluginInstaller,
        installer_args: list[Any] | None = None,
        installer_kwargs: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(plugins_path, source)
        self._installer_class = installer_class
        self._installer_args = installer_args or []
        self._installer_kwargs = installer_kwargs or {}

    async def install(self, overwrite: bool = False) -> Path:
        os.makedirs('storage', exist_ok=True)
        async with ClientSession() as session:
            async with session.get(self.source) as resp:
                resp.raise_for_status()

            with open('storage/plugin', 'wb') as f:
                async for chunk in resp.content.iter_chunked(1024 * 64):
                    f.write(chunk)

        installer_instance = self._installer_class(
            self.plugins_directory,
            Path('storage/plugin').absolute(),
            *self._installer_args,
            **self._installer_kwargs,
        )

        return await installer_instance.install(overwrite=overwrite)


class AiogramPluginInstaller(PluginInstaller[str]):
    def __init__(
        self,
        plugins_path: Path,
        source: str,
        bot: Bot,
        installer_class: type[PluginInstaller] = ZipPluginInstaller,
        installer_args: list[Any] | None = None,
        installer_kwargs: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(plugins_path, source)

        self._bot = bot
        self._installer_class = installer_class
        self._installer_args = installer_args or []
        self._installer_kwargs = installer_kwargs or {}

    @property
    def bot(self) -> Bot:
        return self._bot

    async def install(self, overwrite: bool = False) -> Path:
        file = await self.bot.get_file(self.source)
        os.makedirs('storage', exist_ok=True)
        await self.bot.download_file(file.file_path, 'storage/plugin')

        installer = self._installer_class(
            self.plugins_directory,
            Path('storage/plugin').absolute(),
            *self._installer_args,
            **self._installer_kwargs,
        )

        return await installer.install(overwrite=overwrite)


class Mover:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._temp_path: Path | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def temp_path(self) -> Path | None:
        return self._temp_path

    def __enter__(self) -> Mover:
        if not self.path.exists():
            return self

        index = 0
        temp_name = self.path.parent / f'{self.path.parts[-1]}.old'
        while True:
            if not temp_name.exists():
                break
            index += 1
            temp_name = self.path.parent / f'{self.path.parts[-1]}.old{index}'

        self._temp_path = temp_name
        os.rename(self.path, temp_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._temp_path:
            return

        if exc_type is None:
            if self._temp_path.exists():
                shutil.rmtree(self._temp_path)
                self._temp_path = None
            return

        if self.path.exists():
            if self.temp_path.exists():
                shutil.rmtree(self.path)
            self.temp_path.rename(self.path)

        elif self.temp_path.exists():
            shutil.rmtree(self.temp_path)

        self._temp_path = None
