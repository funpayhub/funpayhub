from __future__ import annotations

import os
import tomllib
from typing import Any, NoReturn, override
from types import MappingProxyType

from funpayhub.lib.properties import Properties
from funpayhub.lib.properties.parameter import ListParameter, StringParameter, ToggleParameter


class AutoResponseEntryProperties(Properties):
    def __init__(self, command: str) -> None:
        super().__init__(
            id=command,
            name=command,
            description='$props.auto_response.*:description',
        )

        self.case_sensitive = self.attach_parameter(
            ToggleParameter(
                id='case_sensitive',
                name='$props.auto_response.*.case_sensitive:name',
                description='$props.auto_response.*.case_sensitive:description',
                default_value=False,
            ),
        )

        self.reply = self.attach_parameter(
            ToggleParameter(
                id='reply',
                name='$props.auto_response.*.reply:name',
                description='$props.auto_response.*.reply:description',
                default_value=True,
            ),
        )

        self.ignore_formatters_errors = self.attach_parameter(
            ToggleParameter(
                id='ignore_formatters_errors',
                name='$props.auto_response.*.ignore_formatters_errors:name',
                description='$props.auto_response.*.ignore_formatters_errors:description',
                default_value=True,
            ),
        )

        self.ignore_hooks_errors = self.attach_parameter(
            ToggleParameter(
                id='ignore_hooks_errors',
                name='$props.auto_response.*.ignore_hooks_errors:name',
                description='$props.auto_response.*.ignore_hooks_errors:description',
                default_value=True,
            ),
        )

        self.react_on_me = self.attach_parameter(
            ToggleParameter(
                id='react_on_me',
                name='$props.auto_response.*.react_on_me:name',
                description='$props.auto_response.*.react_on_me:description',
                default_value=True,
            ),
        )

        self.react_on_others = self.attach_parameter(
            ToggleParameter(
                id='react_on_others',
                name='$props.auto_response.*.react_on_others:name',
                description='$props.auto_response.*.react_on_others:description',
                default_value=True,
            ),
        )

        self.response_text = self.attach_parameter(
            StringParameter(
                id='response_text',
                name='$props.auto_response.*.response_text:name',
                description='$props.auto_response.*.response_text:description',
                default_value='',
            ),
        )

        self.hooks = self.attach_parameter(
            ListParameter(
                id='hooks',
                name='$props.auto_response.*.hooks:name',
                description='$props.auto_response.*.hooks:description',
                default_value=[],
            ),
        )

    @override
    @property
    def parent(self) -> AutoResponseProperties | None:
        return super().parent  # type: ignore

    @override
    @parent.setter
    def parent(self, value: AutoResponseProperties) -> None:
        if not isinstance(value, AutoResponseProperties):
            raise TypeError(
                f'{self.__class__.__name__!r} must be attached only to '
                f'{AutoResponseProperties.__name__!r}.',
            )
        Properties.parent.__set__(self, value)


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

    def attach_parameter(self, parameter: Any) -> NoReturn:
        raise RuntimeError('`AutoDeliveryProperties` does not support parameters.')

    def attach_properties[P: AutoResponseEntryProperties](self, properties: P) -> P:
        if not isinstance(properties, AutoResponseEntryProperties):
            raise ValueError(
                f'{self.__class__.__name__!r} allows attaching only for '
                f'{AutoResponseEntryProperties.__name__!r} instances.',
            )
        return super().attach_properties(properties)

    async def load(self) -> None:
        if not os.path.exists(self.file):  # type: ignore #  always has file
            return
        with open(self.file, 'r', encoding='utf-8') as f:  # type: ignore #  always has file
            data = tomllib.loads(f.read())

        self._entries = {}
        for i in data:
            obj = AutoResponseEntryProperties(command=i)
            await obj._set_values(data[i])
            super().attach_properties(obj)

    def add_entry(self, command: str) -> AutoResponseEntryProperties:
        obj = AutoResponseEntryProperties(command)
        super().attach_properties(obj)
        return obj
