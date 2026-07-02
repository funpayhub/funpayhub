from __future__ import annotations

from funpayhub.lib.translater import ru, en


__all__ = ['GeneralProperties']

from pyconfigtree import Node, FloatParameter, ChoiceParameter, StringParameter, Choice

from funpayhub.app.properties.flags import ParameterFlags

from .validators import proxy_validator
from ...lib.base_app.properties_flags import TelegramUIEmojiFlag


class GeneralProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'general',
            name=ru('Общие'),
            description=en('nodesc'),
            flags={TelegramUIEmojiFlag('🔧')},
        )

        self.language = self._attach_node(
            ChoiceParameter(
                'language',
                name=ru('Язык'),
                description=en('nodesc'),
                choices=(
                    Choice(id='ru', name='🇷🇺 Русский', description='', value='ru'),
                    Choice(id='en', name='🇬🇧 English', description='', value='en'),
                    Choice(id='ua', name='🇺🇦 Українська', description='', value='ua'),
                    Choice(id='banana', name='🍌 Bacunana', description='', value='banana'),
                ),
                fallback_choice_id='ru',
                default_value=Choice(id='ru', name='🇷🇺 Русский', description='', value='ru'),
                flags={TelegramUIEmojiFlag('🌎')},
            ),
        )

        self.proxy = self._attach_node(
            StringParameter(
                'proxy',
                name=ru('Прокси'),
                description=(
                    'Позволяет скрыть ваш IP-адрес при работе с FunPay.\n'
                    'Используется только для запросов к FunPay, на остальной трафик не влияет.\n'
                    'Поддерживаются прокси HTTP(S) и SOCKS5.',
                ),
                default_value='',
                flags={ParameterFlags.PROTECT_VALUE, TelegramUIEmojiFlag('🌐')},
                validator=proxy_validator,
            ),
        )

        self.user_agent = self._attach_node(
            StringParameter(
                'user_agent',
                name=en('User Agent'),
                description=(
                    'Строка, которая сообщает FunPay, какой браузер и устройство используются.\n'
                    'Помогает избежать лишних проверок и блокировок.\n'
                    'Используйте User Agent бразуера, из которого вы взяли golden key.',
                ),
                flags={ParameterFlags.PROTECT_VALUE, TelegramUIEmojiFlag('🌐')},
                default_value='',
            ),
        )

        self.golden_key = self._attach_node(
            StringParameter(
                'golden_key',
                name=ru('Golden Key (токен)'),
                description=(
                    'Ключ доступа к вашему аккаунту FunPay.\n'
                    'Нужен для работы бота и выполнения запросов от вашего имени.',
                ),
                default_value='',
                flags={ParameterFlags.PROTECT_VALUE, TelegramUIEmojiFlag('🔑')},
            ),
        )

        self.runner_request_interval = self._attach_node(
            FloatParameter(
                'runner_request_interval',
                name=ru('Интервал получения событий'),
                description=(
                    'Интервал между запросами к FunPay на получение событий.\n'
                    'Чем меньше интервал, тем быстрее FunPay Hub получает информацию о новых '
                    'сообщениях / заказах и т.д.\n\n',
                ),
                default_value=5.0,
                flags={TelegramUIEmojiFlag('⏳')},
            ),
        )
