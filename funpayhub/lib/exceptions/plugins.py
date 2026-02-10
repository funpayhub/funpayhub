from __future__ import annotations


__all__ = [
    'PluginError',
    'PluginInstallationError',
    'PluginInstantiationError',
    'PluginRepositoryError',
    'PluginRepositoryAlreadyExist',
    'InvalidPluginRepositoryError',
    'SaveRepositoryError',
]

from pathlib import Path

from .base import FunPayHubError


class PluginError(FunPayHubError):
    pass


class PluginRepositoryError(FunPayHubError): ...


class PluginInstallationError(PluginError):
    pass


class PluginInstantiationError(PluginError):
    pass


class PluginRepositoryAlreadyExist(PluginRepositoryError):
    def __init__(self, repository_id: str) -> None:
        self._repository_id = repository_id
        super().__init__('Plugin repository %s already exist.', repository_id)

    @property
    def repository_id(self) -> str:
        return self._repository_id


class InvalidPluginRepositoryError(PluginRepositoryError):
    def __init__(self) -> None:
        super().__init__('Invalid plugin repository.')


class SaveRepositoryError(PluginRepositoryError):
    def __init__(self, repository_id: str, path: str | Path) -> None:
        self._repository_id = repository_id
        self._path = Path(path)
        super().__init__('Unable to save repository %s to %s.', repository_id, str(path))

    @property
    def repository_id(self) -> str:
        return self._repository_id

    @property
    def path(self) -> Path:
        return self._path
