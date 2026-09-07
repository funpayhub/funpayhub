from __future__ import annotations

import json
from typing import Any
from abc import ABC, abstractmethod
from pathlib import Path

from aiohttp import ClientSession
from pydantic import ValidationError

from funpayhub.lib.exceptions import PluginRepositoryLoadingError
from funpayhub.lib.translater import _en

from .types import PluginsRepository


class RepositoryLoader[SOURCE](ABC):
    def __init__(self, source: SOURCE, *args, **kwargs) -> None:
        self._source = source

    @property
    def source(self) -> SOURCE:
        return self._source

    @abstractmethod
    async def load(self) -> PluginsRepository:
        pass


class DictRepositoryLoader(RepositoryLoader[dict[str, Any]]):
    async def load(self) -> PluginsRepository:
        try:
            return PluginsRepository.model_validate(self.source)
        except ValidationError as e:
            raise PluginRepositoryLoadingError(
                _en('Unable to load repository: invalid format.'),
            ) from e


class JSONRepositoryLoader(RepositoryLoader[str]):
    async def load(self) -> PluginsRepository:
        try:
            json_repo = json.loads(self.source)
        except json.JSONDecodeError as e:
            raise PluginRepositoryLoadingError(
                _en('Unable to load repository: JSON decode error.'),
            ) from e

        return await DictRepositoryLoader(json_repo).load()


class FileRepositoryLoader(RepositoryLoader[str | Path]):
    async def load(self) -> PluginsRepository:
        path = Path(self.source)
        if not path.is_file():
            raise PluginRepositoryLoadingError(
                _en('Unable to load repository: %s does not exist.'),
                str(path),
            ) from None

        try:
            with path.open('r', encoding='utf-8') as f:
                data = f.read()
        except Exception as e:
            raise PluginRepositoryLoadingError(
                _en('Unable to load repository: unable to read %s.'),
                str(path),
            ) from e

        return await JSONRepositoryLoader(data).load()


class URLRepositoryLoader(RepositoryLoader[str]):
    def __init__(self, url: str, headers: dict[str, str] | None = None, *args, **kwargs) -> None:
        super().__init__(url, *args, **kwargs)
        self._headers = headers

    async def load(self) -> PluginsRepository:
        return await JSONRepositoryLoader(await self._download_repo_wrapped()).load()

    async def _download_repo(self) -> str:
        async with ClientSession() as s:
            async with s.get(self.source, headers=self._headers, raise_for_status=True) as resp:
                return await resp.text()

    async def _download_repo_wrapped(self) -> str:
        try:
            return await self._download_repo()
        except TimeoutError as e:
            raise PluginRepositoryLoadingError(
                _en('Unable to load repository: download timed out.'),
            ) from e
        except Exception as e:
            raise PluginRepositoryLoadingError(
                _en('Unable to load repository: unexpected error while downloading.'),
            ) from e
