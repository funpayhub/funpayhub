from __future__ import annotations

from typing import TYPE_CHECKING, Any
from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


if TYPE_CHECKING:
    from funpayhub.lib.plugins.manager import PluginManager


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

    Каждый установщик должен при инициализации принимать объект менеджера и ссылку на ресурс.
    Ссылкой на ресурс может быть что угодно, будь то путь до zip архива, URL адресом,
    git-репозиторием и т.п., каждая реализация должна сама проверять, подходит ли ей
    переданный `source`.
    """
    def __init__(self, manager: PluginManager, source: T) -> None:
        self._manager = manager
        self._source = source

    @property
    def manager(self) -> PluginManager:
        return self._manager

    @property
    def source(self) -> T:
        return self._source

    @abstractmethod
    async def install(self, overwrite: bool = False) -> Path:
        pass


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
    def __init__(self, manager: PluginManager, source: str | Path) -> None:
        if not isinstance(source, (str, Path)):
            raise ValueError('Source must be a string or a `pathlib.Path`.')

        source = Path(source)
        super().__init__(manager, source)
        self.check_exists()

    async def install(self, overwrite: bool = False) -> Path:
        self.check_exists()
        with ZipFile(self.source) as zf:
            zip.extractall('plugins')

    def _check_root(self, archive: ZipFile) -> str:
        root_name = None
        for i in archive.infolist():
            path = PurePosixPath(i.filename)
            if path.is_absolute():
                raise PluginInstallationError(
                    'Invalid archive structure: archive contains absolute path %s, '
                    'which is not allowed. All paths must be relative.',
                    path
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
                    curr_root_name
                )

            if root_name is not None and curr_root_name != root_name:
                raise PluginInstallationError(
                    'Invalid archive structure: expected all entries to be under '
                    'root directory %s, but found entry %s outside of it.',
                    root_name,
                    path
                )

            root_name = curr_root_name

        if root_name is None:
            raise PluginInstallationError(
                f'Invalid archive structure: archive is empty.'
            )

        return root_name

    def check_exists(self) -> None:
        if not self.source.exists():
            raise FileNotFoundError(f'Source {self.source} does not exist.')
        if not self.source.is_file():
            raise ValueError(f'Source {self.source} is not a file.')
