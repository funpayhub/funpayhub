from __future__ import annotations

from typing import Any, Self
from pathlib import Path

from pydantic import BaseModel, field_validator, field_serializer
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from funpayhub.lib.plugin.types import PluginAuthor, _WithDescription


class RepoSpecificPluginVersionInfo(BaseModel):
    model_config = {
        'arbitrary_types_allowed': True,
        'extra': 'allow',
    }

    hash: str = ''
    app_version: SpecifierSet
    url: str
    change_log: str = ''

    @field_validator('app_version', mode='before')
    @classmethod
    def convert_hub_version(cls, value: str | SpecifierSet) -> SpecifierSet:
        if isinstance(value, str):
            value = SpecifierSet(value)
        return value

    @field_serializer('app_version', mode='plain')
    def serialize_app_version(self, value: Any) -> str:
        return str(value)


class RepoPluginInfo(_WithDescription):
    model_config = {
        'arbitrary_types_allowed': True,
        'extra': 'allow',
    }

    name: str
    description: str
    author: PluginAuthor | None = None
    repo: str | None = None
    versions: dict[Version, RepoSpecificPluginVersionInfo]

    @field_validator('versions', mode='before')
    @classmethod
    def convert_to_version(cls, value: dict[str | Version, Any]) -> dict[Version, Any]:
        return {Version(k) if not isinstance(k, Version) else k: v for k, v in value.items()}

    @field_serializer('versions', mode='wrap')
    def convert_version(self, value: dict[Any, Any], handler: Any) -> dict[str, Any]:
        val = {str(k): v for k, v in value.items()}
        return handler(val)


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
