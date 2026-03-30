from __future__ import annotations

from typing import Any
from types import MappingProxyType

from funpayhub.lib.properties import (
    Properties,
    StringParameter,
    ToggleParameter,
)
from funpayhub.lib.translater import _
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag

from funpayhub.app.properties.flags import FormattersQueryFlag


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
                    'Вкл.: различает заглавные и строчные.\nВыкл.: регистр игнорируется.',
                ),
                default_value=False,
            ),
        )

        self.reply = self.attach_node(
            ToggleParameter(
                id='reply',
                name=_('Отвечать'),
                description=_(
                    'Вкл.: бот отвечает на команду (если указан текст ответа).\n'
                    'Выкл.: бот не отвечает на команду.',
                ),
                default_value=True,
            ),
        )

        self.ignore_formatters_errors = self.attach_node(
            ToggleParameter(
                id='ignore_formatters_errors',
                name=_('Игнорировать ошибки форматтеров'),
                description=_(
                    'Вкл.: если произошла ошибка в каком-либо форматтере, '
                    'бот подставляет вместо него пустоту.\n'
                    'Выкл.: бот не отправляет сообщение, если произошла ошибка хотя бы в '
                    '1 из форматтеров.',
                ),
                default_value=True,
            ),
        )

        self.react_on_me = self.attach_node(
            ToggleParameter(
                id='react_on_me',
                name=_('Реагировать, если отправитель - я'),
                description=_(
                    'Вкл.: бот обрабатывает команду, если ее отправили вы.\n'
                    'Выкл.: бот не обрабатывает команду, если ее отправили вы.',
                ),
                default_value=True,
            ),
        )

        self.react_on_others = self.attach_node(
            ToggleParameter(
                id='react_on_others',
                name=_('Реагировать, если отправитель - не я'),
                description=_(
                    'Вкл.: бот обрабатывает команду, если ее отправили не вы.\n'
                    'Выкл.: бот не обрабатывает команду, если ее отправили не вы.',
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
                flags=[FormattersQueryFlag('fph:general|fph:message')],
            ),
        )


class AutoResponseProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='auto_response',
            name=_('Команды'),
            description=_('nodesc'),
            file='config/auto_response.toml',
            flags=[TelegramUIEmojiFlag('💬')],
        )

    @property
    def entries(self) -> MappingProxyType[str, AutoResponseEntryProperties]:
        return super().entries  # type: ignore

    async def load_from_dict(self, properties_dict: dict[str, Any]) -> None:
        await super().load_from_dict(properties_dict)
        for i in properties_dict:
            obj = AutoResponseEntryProperties(command=i)
            await obj.load_from_dict(properties_dict[i])
            self.attach_node(obj, replace=True)

    def add_entry(self, command: str) -> AutoResponseEntryProperties:
        obj = AutoResponseEntryProperties(command)
        super().attach_node(obj)
        return obj
