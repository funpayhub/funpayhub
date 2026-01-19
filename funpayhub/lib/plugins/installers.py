from __future__ import annotations

from typing import TYPE_CHECKING, Any
from abc import ABC, abstractmethod
from pathlib import Path
from zipfile import ZipFile


if TYPE_CHECKING:
    from funpayhub.lib.plugins.manager import PluginManager


class PluginInstaller[T: Any](ABC):
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
    async def install(self) -> Path:
        pass


class ZipPluginInstaller(PluginInstaller[str | Path]):
    def __init__(self, manager: PluginManager, source: str | Path) -> None:
        if not isinstance(source, (str, Path)):
            raise ValueError('Source must be a string or a `pathlib.Path`.')

        source = Path(source)
        super().__init__(manager, source)
        self.check_exists()

    async def install(self) -> Path:
        self.check_exists()
        with ZipFile(self.source) as zip:
            zip.extractall('plugins')

    def check_exists(self) -> None:
        if not self.source.exists():
            raise FileNotFoundError(f'Source {self.source} does not exist.')
        if not self.source.is_file():
            raise ValueError(f'Source {self.source} is not a file.')
