from __future__ import annotations

from typing import Any
from types import MappingProxyType

from pyconfigtree import Node, StringParameter, BoolParameter
from pyconfigtree.source.toml import TOMLSource
from funpayhub.lib.translater import ru, en
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag

from funpayhub.app.properties.flags import FormattersQueryFlag


class AutoResponseEntryProperties(Node):
    def __init__(self, command: str) -> None:
        super().__init__(command, name=command, description=ru('Настройки реакции на команду.'))

        self.response_text = self._attach_node(
            StringParameter(
                'response_text',
                name=ru('Текст ответа'),
                description=ru('Текст ответа на команду.'),
                default_value='',
                flags={FormattersQueryFlag('fph:general|fph:message')},
            ),
        )

        self.reply = self._attach_node(
            BoolParameter(
                'reply',
                name=ru('Включить'),
                description=ru(
                    'Вкл.: бот отвечает на команду (если указан текст ответа).\n'
                    'Выкл.: бот не отвечает на команду.',
                ),
                default_value=True,
            ),
        )

        self.case_sensitive = self._attach_node(
            BoolParameter(
                'case_sensitive',
                name=ru('Учитывать регистр'),
                description=ru(
                    'Вкл.: различает заглавные и строчные.\nВыкл.: регистр игнорируется.',
                ),
                default_value=False,
            ),
        )

        self.ignore_formatters_errors = self._attach_node(
            BoolParameter(
                'ignore_formatters_errors',
                name=ru('Игнорировать ошибки форматтеров'),
                description=ru(
                    'Вкл.: если произошла ошибка в каком-либо форматтере, '
                    'бот подставляет вместо него пустоту.\n'
                    'Выкл.: бот не отправляет сообщение, если произошла ошибка хотя бы в '
                    '1 из форматтеров.',
                ),
                default_value=True,
            ),
        )

        self.react_on_me = self._attach_node(
            BoolParameter(
                'react_on_me',
                name=ru('Реагировать, если отправитель - я'),
                description=ru(
                    'Вкл.: бот обрабатывает команду, если ее отправили вы.\n'
                    'Выкл.: бот не обрабатывает команду, если ее отправили вы.',
                ),
                default_value=True,
            ),
        )

        self.react_on_others = self._attach_node(
            BoolParameter(
                'react_on_others',
                name=ru('Реагировать, если отправитель - не я'),
                description=ru(
                    'Вкл.: бот обрабатывает команду, если ее отправили не вы.\n'
                    'Выкл.: бот не обрабатывает команду, если ее отправили не вы.',
                ),
                default_value=True,
            ),
        )


class AutoResponseProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'auto_response',
            name=ru('Команды'),
            description=en('nodesc'),
            source=TOMLSource('config/auto_response.toml'),
            flags={TelegramUIEmojiFlag('💬')},
        )

    @property
    def entries(self) -> MappingProxyType[str, AutoResponseEntryProperties]:
        return super().subnodes  # type: ignore

    async def load_from_dict(
        self,
        data_dict: dict[str, Any],
        validate: bool = True,
        run_hook: bool = False,
    ) -> None:
        await super().load_from_dict(data_dict)
        for i in data_dict:
            if i in self.subnodes:
                self._detach_node(i)
            obj = AutoResponseEntryProperties(command=i)
            await obj.load_from_dict(data_dict[i])
            self._attach_node(obj)

    async def add_node(self, command: str) -> AutoResponseEntryProperties:
        obj = AutoResponseEntryProperties(command)
        await self.attach_node(obj)
        return obj
