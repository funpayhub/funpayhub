from __future__ import annotations


__all__ = [
    'PluginProperties',
]


from typing import TypeVar

from funpayhub.lib.properties import Properties, ListParameter


T = TypeVar('T', bound=Properties)


class PluginProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='plugin_properties',
            name='$props:plugin_properties:name',
            description='$props:plugin_properties:description',
        )

        self.disabled_plugins = self.attach_node(
            ListParameter(
                id='disabled_plugins',
                name='$props:plugin_properties:disabled_plugins:name',
                description='$props:plugin_properties:disabled_plugins:description',
                default_factory=list,
            ),
        )
