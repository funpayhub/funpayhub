from __future__ import annotations

from pathlib import Path
from typing import Any, Self

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pydantic import BaseModel, field_validator

from funpayhub.lib.plugins.types import _WithDescription


class RepoSpecificPluginVersionInfo(BaseModel):
    model_config = {
        'arbitrary_types_allowed': True,
        'extra': 'allow',
    }

    app_version: SpecifierSet
    url: str
    change_log: str = ''

    @field_validator('app_version', mode='before')
    @classmethod
    def convert_hub_version(cls, value: str | SpecifierSet) -> SpecifierSet:
        if isinstance(value, str):
            value = SpecifierSet(value)
        return value


class RepoPluginInfo(_WithDescription):
    model_config = {
        'arbitrary_types_allowed': True,
        'extra': 'allow',
    }

    name: str
    description: str
    versions: dict[Version, RepoSpecificPluginVersionInfo]
    more_versions: str = ''

    @field_validator('versions', mode='before')
    @classmethod
    def convert_to_version(cls, value: dict[str | Version, Any]) -> dict[Version, Any]:
        return {Version(k) if not isinstance(k, Version) else k: v for k, v in value.items()}


class PluginsRepository(_WithDescription):
    model_config = {
        'arbitrary_types_allowed': True,
        'extra': 'allow',
    }

    version: int = 1
    id: str
    url: str
    name: str
    description: str
    plugins: dict[str, RepoPluginInfo]

    @classmethod
    async def from_dict(cls, data: dict[str, Any]) -> Self:
        from .loaders import DictRepositoryLoader
        return await DictRepositoryLoader(data).load()

    @classmethod
    async def from_json(cls, data: str) -> Self:
        from .loaders import JSONRepositoryLoader
        return await JSONRepositoryLoader(data).load()

    @classmethod
    async def from_file(cls, path: str | Path) -> Self:
        from .loaders import FileRepositoryLoader
        return await FileRepositoryLoader(path).load()

    @classmethod
    async def from_url(cls, url: str, headers: dict[str, str] | None = None) -> Self:
        from .loaders import URLRepositoryLoader
        return await URLRepositoryLoader(url, headers).load()