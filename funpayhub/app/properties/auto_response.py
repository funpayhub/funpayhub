from __future__ import annotations

import os
import tomllib
from types import MappingProxyType

from funpayhub.lib.properties import (
    Node,
    Properties,
    ListParameter,
    StringParameter,
    ToggleParameter,
)


class AutoResponseEntryProperties(Properties):
    def __init__(self, command: str) -> None:
        super().__init__(
            id=command,
            name=command,
            description='$props.auto_response.*:description',
        )

        self.case_sensitive = self.attach_node(
            ToggleParameter(
                id='case_sensitive',
                name='$props.auto_response.*.case_sensitive:name',
                description='$props.auto_response.*.case_sensitive:description',
                default_value=False,
            ),
        )

        self.reply = self.attach_node(
            ToggleParameter(
                id='reply',
                name='$props.auto_response.*.reply:name',
                description='$props.auto_response.*.reply:description',
                default_value=True,
            ),
        )

        self.ignore_formatters_errors = self.attach_node(
            ToggleParameter(
                id='ignore_formatters_errors',
                name='$props.auto_response.*.ignore_formatters_errors:name',
                description='$props.auto_response.*.ignore_formatters_errors:description',
                default_value=True,
            ),
        )

        self.ignore_hooks_errors = self.attach_node(
            ToggleParameter(
                id='ignore_hooks_errors',
                name='$props.auto_response.*.ignore_hooks_errors:name',
                description='$props.auto_response.*.ignore_hooks_errors:description',
                default_value=True,
            ),
        )

        self.react_on_me = self.attach_node(
            ToggleParameter(
                id='react_on_me',
                name='$props.auto_response.*.react_on_me:name',
                description='$props.auto_response.*.react_on_me:description',
                default_value=True,
            ),
        )

        self.react_on_others = self.attach_node(
            ToggleParameter(
                id='react_on_others',
                name='$props.auto_response.*.react_on_others:name',
                description='$props.auto_response.*.react_on_others:description',
                default_value=True,
            ),
        )

        self.response_text = self.attach_node(
            StringParameter(
                id='response_text',
                name='$props.auto_response.*.response_text:name',
                description='$props.auto_response.*.response_text:description',
                default_value='',
            ),
        )

        self.hooks = self.attach_node(
            ListParameter(
                id='hooks',
                name='$props.auto_response.*.hooks:name',
                description='$props.auto_response.*.hooks:description',
                default_factory=list,
            ),
        )


class AutoResponseProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='auto_response',
            name='$props.auto_response:name',
            description='$props.auto_response:description',
            file='config/auto_response.toml',
        )

    @property
    def entries(self) -> MappingProxyType[str, AutoResponseEntryProperties]:
        return super().entries  # type: ignore

    def attach_node[P: Node](self, node: P) -> P:
        if not isinstance(node, AutoResponseEntryProperties):
            raise ValueError(
                f'{self.__class__.__name__!r} allows attaching only for '
                f'{AutoResponseEntryProperties.__name__!r} instances.',
            )
        return super().attach_node(node)

    async def load(self) -> None:
        if not os.path.exists(self.file):  # type: ignore #  always has file
            return
        with open(self.file, 'r', encoding='utf-8') as f:  # type: ignore #  always has file
            data = tomllib.loads(f.read())

        self._nodes = {}
        for i in data:
            obj = AutoResponseEntryProperties(command=i)
            await obj._set_values(data[i])
            super().attach_node(obj)

    def add_entry(self, command: str) -> AutoResponseEntryProperties:
        obj = AutoResponseEntryProperties(command)
        super().attach_node(obj)
        return obj
