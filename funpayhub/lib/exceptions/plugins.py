from __future__ import annotations


__all__ = [
    'PluginError',
    'PluginInstallationError',
    'PluginInstantiationError',
    'PluginRepositoryError',
    'PluginRepositoryAlreadyExist',
    'InvalidPluginRepositoryError',
    'SaveRepositoryError',
    'RemoveRepositoryError',
    'PluginRepositoryLoadingError',
]

from pathlib import Path

from funpayhub.lib.translater import _en

from .base import FunPayHubError


class PluginError(FunPayHubError):
    pass


class PluginRepositoryError(FunPayHubError): ...


class PluginInstallationError(PluginError):
    pass


class PluginInstantiationError(PluginError):
    pass


class PluginRepositoryLoadingError(PluginRepositoryError): ...


class PluginRepositoryAlreadyExist(PluginRepositoryError):
    def __init__(self, repository_id: str) -> None:
        self._repository_id = repository_id
        super().__init__(_en('Plugin repository %s already exist.'), repository_id)

    @property
    def repository_id(self) -> str:
        return self._repository_id


class InvalidPluginRepositoryError(PluginRepositoryError):
    def __init__(self) -> None:
        super().__init__(_en('Invalid plugin repository.'))


class SaveRepositoryError(PluginRepositoryError):
    def __init__(self, repository_id: str, path: str | Path) -> None:
        self._repository_id = repository_id
        self._path = Path(path)
        super().__init__(_en('Unable to save repository %s to %s.'), repository_id, str(path))

    @property
    def repository_id(self) -> str:
        return self._repository_id

    @property
    def path(self) -> Path:
        return self._path


class RemoveRepositoryError(PluginRepositoryError):
    def __init__(self, repository_id: str, path: str | Path | None) -> None:
        self._repository_id = repository_id
        self._path = Path(path) if path is not None else None

        super().__init__(
            _en('Unable to remove repository %s. (file: %s).'),
            repository_id,
            str(path),
        )

    @property
    def repository_id(self) -> str:
        return self._repository_id

    @property
    def path(self) -> Path | None:
        return self._path
