from __future__ import annotations


__all__ = [
    'AutoResponseProperties',
    'CommandNode',
]

from typing import Any
from types import MappingProxyType

from pyconfigtree import Properties, BoolParameter, StringParameter
from hubplatform.i18n import I18nString
from pyconfigtree.source.toml import TOMLSource


class CommandNode(Properties):
    def __init__(self, command: str) -> None:
        super().__init__(
            node_id=command,
            name=command,
            description=I18nString(
                key='funpayhub.properties.funpay_component.auto_response.name',
                fallback=f'Настройки реакции на команду {command}.',
                kwargs={'command': command},
            ),
        )

        self.reply = self.attach_node(
            BoolParameter(
                node_id='reply',
                name=I18nString('Включить'),
                description=I18nString(
                    'Вкл.: бот отвечает на команду (если указан текст ответа).\n'
                    'Выкл.: бот не отвечает на команду.',
                ),
                default_value=True,
            ),
        )

        self.response_text = self.attach_node(
            StringParameter(
                node_id='response_text',
                name=I18nString('Текст ответа'),
                description=I18nString('Текст ответа на команду.'),
                default_value='',
            ),
        )

        self.case_sensitive = self.attach_node(
            BoolParameter(
                node_id='case_sensitive',
                name=I18nString('Учитывать регистр'),
                description=I18nString(
                    'Вкл.: различает заглавные и строчные.\nВыкл.: регистр игнорируется.',
                ),
                default_value=False,
            ),
        )

        self.ignore_expression_errors = self.attach_node(
            BoolParameter(
                node_id='ignore_expression_errors',
                name=I18nString('Игнорировать ошибки выражений'),
                description=I18nString(
                    'Вкл.: если произошла ошибка в каком-либо форматтере, '
                    'бот подставляет вместо него пустоту.\n'
                    'Выкл.: бот не отправляет сообщение, если произошла ошибка хотя бы в '
                    '1 из форматтеров.',
                ),
                default_value=True,
            ),
        )

        self.react_on_me = self.attach_node(
            BoolParameter(
                node_id='react_on_me',
                name=I18nString('Реагировать, если отправитель - я'),
                description=I18nString(
                    'Вкл.: бот обрабатывает команду, если ее отправили вы.\n'
                    'Выкл.: бот не обрабатывает команду, если ее отправили вы.',
                ),
                default_value=True,
            ),
        )

        self.react_on_others = self.attach_node(
            BoolParameter(
                node_id='react_on_others',
                name=I18nString('Реагировать, если отправитель - не я'),
                description=I18nString(
                    'Вкл.: бот обрабатывает команду, если ее отправили не вы.\n'
                    'Выкл.: бот не обрабатывает команду, если ее отправили не вы.',
                ),
                default_value=True,
            ),
        )


class AutoResponseProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='auto_response',
            name=I18nString('Команды'),
            description=I18nString('nodesc'),
            source=TOMLSource('config/funpay/auto_response.toml'),
            metadata={'emoji': '💬'},
        )

    @property
    def entries(self) -> MappingProxyType[str, CommandNode]:
        return super().entries  # type: ignore

    async def load_from_dict(
        self,
        data_dict: dict[str, Any],
        validate: bool = True,
        run_hook: bool = False,
    ) -> None:
        for i in data_dict:
            obj = CommandNode(command=i)
            await obj.load_from_dict(data_dict[i], validate=validate, run_hook=run_hook)
            self.attach_node(obj)

    async def add_command_node(self, command: str) -> CommandNode:
        obj = CommandNode(command)
        return await self.attach_node_with_hooks(obj)
