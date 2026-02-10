from __future__ import annotations


__all__ = [
    'PluginManifest',
    'LoadedPlugin',
]


from typing import TYPE_CHECKING, Self
from dataclasses import dataclass
from pathlib import Path

from pydantic import Field, BaseModel, field_validator, model_validator
from packaging.version import Version
from packaging.specifiers import SpecifierSet

if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties


class _WithDescription(BaseModel):
    description: str = Field(default='')

    @model_validator(mode='after')
    def check_dependencies(self) -> Self:
        if not self.model_extra:
            return self

        for k, v in self.model_extra.items():
            if not k.startswith('description_'):
                continue
            if not isinstance(v, str) or len(v.strip()) == 0:
                raise ValueError(f'{k} must be non-empty string.')
        return self

    def get_description(self, locale: str | None = None) -> str:
        if locale is None:
            return self.description

        if f'description_{locale.lower()}' in self.model_extra:
            return self.model_extra[f'description_{locale.lower()}']
        return self.description


class PluginManifest(_WithDescription):
    model_config = {
        'extra': 'allow',
        'frozen': True,
        'arbitrary_types_allowed': True,
    }

    manifest: int
    plugin_version: Version
    app_version: SpecifierSet
    plugin_id: str
    name: str
    repo: str | None = Field(default=None)
    entry_point: str = Field(pattern=r'^([a-zA-Z_][a-zA-Z0-9_]*\.)+[a-zA-Z_][a-zA-Z0-9_]*$')
    author: PluginAuthor | None = Field(default=None)
    dependencies: list[str] = Field(default_factory=list)
    locales_path: str | None = None

    @field_validator('plugin_version', mode='before')
    @classmethod
    def convert_version(cls, value: str | Version) -> Version:
        if isinstance(value, str):
            value = Version(value)
        return value

    @field_validator('app_version', mode='before')
    @classmethod
    def convert_hub_version(cls, value: str | SpecifierSet) -> SpecifierSet:
        if isinstance(value, str):
            value = SpecifierSet(value)
        return value


class PluginAuthor(BaseModel):
    model_config = {
        'extra': 'allow',
        'frozen': True,
    }

    name: str | None = Field(default=None)
    mail: str | None = Field(default=None)
    website: str | None = Field(default=None)
    social: dict[str, str] | None = Field(default=None)


@dataclass
class LoadedPlugin[PluginCLS]:
    path: Path
    manifest: PluginManifest
    plugin: PluginCLS | None
    properties: Properties | None = None
    error: Exception | None = None
