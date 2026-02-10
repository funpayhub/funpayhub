from __future__ import annotations

__all__ = ['RepositoriesManager']


import json
from copy import copy
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from funpayhub.lib.exceptions import InvalidPluginRepositoryError, PluginRepositoryAlreadyExist, TranslatableException, \
    SaveRepositoryError, RemoveRepositoryError
from funpayhub.lib.plugins.repository.types import PluginsRepository
from loggers import plugins as logger


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
        overwrite: bool = False,
    ) -> PluginsRepository:
        if not isinstance(repository, PluginsRepository):
            try:
                repository = PluginsRepository.model_validate(repository)
            except ValidationError as e:
                raise InvalidPluginRepositoryError() from e

        if save:
            if repository.id in self._repositories and not overwrite:
                raise PluginRepositoryAlreadyExist(repository.id)
            self.save_repository(repository)

        if register:
            self.register_repository(repository, overwrite=overwrite)

        return repository

    def register_repository(self, repository: PluginsRepository, overwrite: bool = False) -> None:
        if repository.id in self._repositories and not overwrite:
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
