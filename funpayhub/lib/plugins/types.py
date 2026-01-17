from __future__ import annotations


__all__ = [
    'PluginManifest',
    'Plugin',
    'LoadedPlugin',
]


from typing import TYPE_CHECKING, Self
from dataclasses import dataclass
from pathlib import Path

from pydantic import Field, BaseModel, field_validator, model_validator
from packaging.version import Version
from packaging.specifiers import SpecifierSet


if TYPE_CHECKING:
    from aiogram import Router as TGRouter
    from funpaybotengine import Router as FPRouter

    from funpayhub.app.main import FunPayHub
    from funpayhub.lib.properties import Properties
    from funpayhub.app.dispatching import Router as HubRouter
    from funpayhub.lib.telegram.ui import (
        MenuBuilder,
        ButtonBuilder,
        MenuModification,
        ButtonModification,
    )
    from funpayhub.lib.hub.text_formatters import Formatter
    from funpayhub.lib.telegram.commands_registry import Command


class PluginManifest(BaseModel):
    model_config = {
        'extra': 'allow',
        'frozen': True,
        'arbitrary_types_allowed': True,
    }

    manifest: int
    plugin_version: Version
    hub_version: SpecifierSet
    plugin_id: str
    name: str
    repo: str | None = Field(default=None)
    description: str = Field(default='')
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

    @field_validator('hub_version', mode='before')
    @classmethod
    def convert_hub_version(cls, value: str | SpecifierSet) -> SpecifierSet:
        if isinstance(value, str):
            value = SpecifierSet(value)
        return value

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


class PluginAuthor(BaseModel):
    model_config = {
        'extra': 'allow',
        'frozen': True,
    }

    name: str | None = Field(default=None)
    mail: str | None = Field(default=None)
    website: str | None = Field(default=None)
    social: dict[str, str] | None = Field(default=None)


class Plugin:
    def __init__(
        self,
        manifest: PluginManifest,
        hub: FunPayHub,
    ) -> None:
        self._manifest = manifest
        self._hub = hub

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    @property
    def hub(self) -> FunPayHub:
        return self._hub

    async def pre_setup(self) -> Properties:
        raise NotImplementedError()

    async def properties(self) -> Properties:
        raise NotImplementedError()

    async def setup_properties(self) -> None:
        raise NotImplementedError()

    async def formatters(self) -> type[Formatter] | list[type[Formatter]] | None:
        raise NotImplementedError()

    async def setup_formatters(self) -> None:
        raise NotImplementedError()

    async def hub_routers(self) -> HubRouter | list[HubRouter]:
        raise NotImplementedError()

    async def setup_hub_routers(self) -> None:
        raise NotImplementedError()

    async def funpay_routers(self) -> FPRouter | list[FPRouter]:
        raise NotImplementedError()

    async def setup_funpay_routers(self) -> None:
        raise NotImplementedError()

    async def telegram_routers(self) -> TGRouter | list[TGRouter]:
        raise NotImplementedError()

    async def setup_telegram_routers(self) -> None:
        raise NotImplementedError()

    async def menus(self) -> type[MenuBuilder] | list[type[MenuBuilder]]:
        raise NotImplementedError()

    async def setup_menus(self) -> None:
        raise NotImplementedError()

    async def buttons(self) -> ButtonBuilder | list[type[ButtonBuilder]]:
        raise NotImplementedError()

    async def setup_buttons(self) -> None:
        raise NotImplementedError()

    async def menu_modifications(
        self,
    ) -> dict[str, type[MenuModification] | list[type[MenuModification]]]:
        raise NotImplementedError()

    async def setup_menu_modifications(self) -> None:
        raise NotImplementedError()

    async def button_modifications(
        self,
    ) -> dict[str, type[ButtonModification] | list[type[ButtonModification]]]:
        raise NotImplementedError()

    async def setup_button_modifications(self) -> None:
        raise NotImplementedError()

    async def commands(self) -> Command | list[Command] | None:
        raise NotImplementedError()

    async def setup_commands(self) -> None:
        raise NotImplementedError()

    async def post_setup(self) -> None:
        raise NotImplementedError()


@dataclass
class LoadedPlugin:
    path: Path
    manifest: PluginManifest
    plugin: Plugin | None
    properties: Properties | None = None
