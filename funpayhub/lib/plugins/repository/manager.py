from __future__ import annotations

from funpayhub.lib.translater import _en


__all__ = ['RepositoriesManager']


from copy import copy
from pathlib import Path

from loggers import plugins as logger

from funpayhub.lib.exceptions import (
    SaveRepositoryError,
    RemoveRepositoryError,
    TranslatableException,
    PluginRepositoryAlreadyExist,
)
from funpayhub.lib.plugins.repository.types import PluginsRepository
from funpayhub.lib.plugins.repository.loaders import FileRepositoryLoader


class RepositoriesManager:
    def __init__(self, repositories_path: str | Path) -> None:
        self._repositories_path = Path(repositories_path)
        self._repositories: dict[str, PluginsRepository] = {}

    def register_repository(
        self,
        repository: PluginsRepository,
        overwrite: bool = False,
        save: bool = True,
    ) -> None:
        if repository.id in self._repositories and not overwrite:
            raise PluginRepositoryAlreadyExist(repository.id)
        if save:
            self.save_repository(repository)

        self._repositories[repository.id] = repository

    def _save_repository(self, repository: PluginsRepository, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as f:
            f.write(repository.model_dump_json(indent=4))

    async def _load_repositories(self) -> None:
        logger.info(_en('Loading plugins repositories from %s...'), str(self._repositories_path))
        if not self._repositories_path.exists():
            return
        if self._repositories_path.is_file():
            return

        for i in self._repositories_path.iterdir():
            if i.is_dir():
                logger.debug(_en('%s is a directory. Skipping.'), str(i))
                continue
            if not i.suffix == '.json':
                logger.warning(_en('%s is not a JSON file. Skipping.'), str(i))
                continue

            logger.info(_en('Loading plugins repository from %s...'), str(i))
            try:
                repo = await FileRepositoryLoader(i).load()
                if repo.id != i.stem:
                    logger.warning(
                        _en('Repository ID %s does not match repo file %s. Skipping.'),
                        repo.id,
                        i.name,
                    )
                    continue
                self.register_repository(repo, save=False)
            except Exception as e:
                if isinstance(e, TranslatableException):
                    logger.error(e.message, *e.args, exc_info=True)
                else:
                    logger.error(
                        _en('An error occurred while loading plugin repository from %s.'),
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
