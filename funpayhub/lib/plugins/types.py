from __future__ import annotations


__all__ = [
    'PluginManifest',
    'Plugin',
    'LoadedPlugin',
]


from typing import TYPE_CHECKING
from dataclasses import dataclass

from pydantic import Field, BaseModel, field_validator
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from funpayhub.lib.properties import Properties
from funpayhub.app.dispatching import Router
from funpayhub.lib.telegram.ui import (
    MenuBuilder,
    ButtonBuilder,
    MenuModification,
    ButtonModification,
)


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


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
    description: str = Field(default='')
    entry_point: str = Field(pattern=r'^([a-zA-Z_][a-zA-Z0-9_]*\.)+[a-zA-Z_][a-zA-Z0-9_]*$')
    author: PluginAuthor | None = Field(default=None)
    dependencies: list[str] = Field(default_factory=list)
    locales_path: list[str] = Field(default_factory=list)

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

    async def hub_routers(self) -> Router | list[Router]:
        raise NotImplementedError()

    async def setup_hub_routers(self) -> None:
        raise NotImplementedError()

    async def funpay_routers(self) -> Router | list[Router]:
        raise NotImplementedError()

    async def setup_funpay_routers(self) -> None:
        raise NotImplementedError()

    async def telegram_routers(self) -> Router | list[Router]:
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

    async def post_setup(self) -> None:
        raise NotImplementedError()


@dataclass
class LoadedPlugin:
    manifest: PluginManifest
    plugin: Plugin
    properties: Properties | None = None
