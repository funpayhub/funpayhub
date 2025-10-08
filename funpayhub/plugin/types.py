from pydantic import BaseModel, field_validator, field_serializer
from packaging.version import Version
from packaging.specifiers import SpecifierSet


class PluginManifest(BaseModel):
    model_config = {
        'arbitrary_types_allowed': True
    }

    id: str
    name: str
    description: str
    version: Version
    hub_version: SpecifierSet

    @field_validator('version', mode='before')
    @staticmethod
    def _version_validator(v: str) -> Version:
        return Version(v)

    @field_serializer('version')
    @staticmethod
    def _version_serializer(v: Version) -> str:
        return str(v)

    @field_validator('hub_version', mode='before')
    @staticmethod
    def _hub_version_validator(v: str) -> SpecifierSet:
        return SpecifierSet(v)

    @field_serializer('hub_version')
    @staticmethod
    def _hub_version_serializer(v: SpecifierSet) -> str:
        return str(v)


class PluginManager:
    def __init__(self, version: str | Version):
        self._version = version if isinstance(version, Version) else Version(version)
        self.plugins: dict[str, PluginManifest] = {}

    def add_plugin(self, plugin: PluginManifest):
        if plugin.id in self.plugins:
            raise ValueError(f'Plugin {plugin.id} already exists')  # todo

        if not plugin.hub_version.contains(self._version):
            raise ValueError(f'Unsupported version')

        self.plugins[plugin.id] = plugin