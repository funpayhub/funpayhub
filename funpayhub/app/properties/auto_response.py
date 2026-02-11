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
from funpayhub.lib.translater import _


class AutoResponseEntryProperties(Properties):
    def __init__(self, command: str) -> None:
        super().__init__(
            id=command,
            name=command,
            description=_('Настройки реакции на команду.'),
        )

        self.case_sensitive = self.attach_node(
            ToggleParameter(
                id='case_sensitive',
                name=_('Учитывать регистр'),
                description=_(
                    'Вкл.: различает заглавные и строчные.\nВыкл.: регистр игнорируется.'
                ),
                default_value=False,
            ),
        )

        self.reply = self.attach_node(
            ToggleParameter(
                id='reply',
                name=_('Отвечать'),
                description=_(
                    'Вкл.: бот отвечает на команду (если указан текст ответа).\nВыкл.: бот не отвечает на команду.'
                ),
                default_value=True,
            ),
        )

        self.ignore_formatters_errors = self.attach_node(
            ToggleParameter(
                id='ignore_formatters_errors',
                name=_('Игнорировать ошибки форматтеров'),
                description=_(
                    'Вкл.: если произошла ошибка в каком-либо форматтере, бот подставляет вместо него пустоту.\nВыкл.: бот не отправляет сообщение, если произошла ошибка хотя бы в 1 из форматтеров.'
                ),
                default_value=True,
            ),
        )

        self.ignore_hooks_errors = self.attach_node(
            ToggleParameter(
                id='ignore_hooks_errors',
                name=_('Игнорировать ошибки хуков'),
                description=_(
                    'Вкл.: если произошла ошибка в каком-либо хуке, бот продолжает выполнять другие хуки.\nВыкл.: бот прерывает цепочку выполнения хуков, если хотя бы 1 из хуков завершился с ошибкой.'
                ),
                default_value=True,
            ),
        )

        self.react_on_me = self.attach_node(
            ToggleParameter(
                id='react_on_me',
                name=_('Реагировать, если отправитель - я'),
                description=_(
                    'Вкл.: бот обрабатывает команду, если ее отправили вы.\nВыкл.: бот не обрабатывает команду, если ее отправили вы.'
                ),
                default_value=True,
            ),
        )

        self.react_on_others = self.attach_node(
            ToggleParameter(
                id='react_on_others',
                name=_('Реагировать, если отправитель - не я'),
                description=_(
                    'Вкл.: бот обрабатывает команду, если ее отправили не вы.\nВыкл.: бот не обрабатывает команду, если ее отправили не вы.'
                ),
                default_value=True,
            ),
        )

        self.response_text = self.attach_node(
            StringParameter(
                id='response_text',
                name=_('Текст ответа'),
                description=_('Текст ответа на команду.'),
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
            name=_('💬 Команды'),
            description=_('nodesc'),
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
