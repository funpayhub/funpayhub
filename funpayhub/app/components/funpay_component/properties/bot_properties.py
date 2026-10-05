from __future__ import annotations


__all__ = ['FunPayBotProperties']

from pyconfigtree import Properties, FloatParameter, StringParameter
from hubplatform.i18n import I18nString


# from .validators import proxy_validator


class FunPayBotProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='bot',
            name=I18nString('Аккаунт'),
            description=I18nString('nodesc'),
            metadata={'emoji': '🔧'},
        )

        self.proxy = self.attach_node(
            StringParameter(
                node_id='proxy',
                name=I18nString('Прокси'),
                description=I18nString(
                    'Позволяет скрыть ваш IP-адрес при работе с FunPay.\n'
                    'Используется только для запросов к FunPay, на остальной трафик не влияет.\n'
                    'Поддерживаются прокси HTTP(S) и SOCKS5.',
                ),
                default_value='',
                metadata={'emoji': '🌐', 'protect_value': True},
                # validator=proxy_validator,
            ),
        )

        self.user_agent = self.attach_node(
            StringParameter(
                node_id='user_agent',
                name=I18nString('User Agent'),
                description=I18nString(
                    'Строка, которая сообщает FunPay, какой браузер и устройство используются.\n'
                    'Помогает избежать лишних проверок и блокировок.\n'
                    'Используйте User Agent бразуера, из которого вы взяли golden key.',
                ),
                metadata={'emoji': '🌐', 'protect_value': True},
                default_value='',
            ),
        )

        self.golden_key = self.attach_node(
            StringParameter(
                node_id='golden_key',
                name=I18nString('Golden Key (токен)'),
                description=I18nString(
                    'Ключ доступа к вашему аккаунту FunPay.\n'
                    'Нужен для работы бота и выполнения запросов от вашего имени.',
                ),
                default_value='',
                metadata={'emoji': '🔑', 'protect_value': True},
            ),
        )

        self.runner_request_interval = self.attach_node(
            FloatParameter(
                node_id='runner_request_interval',
                name=I18nString('Интервал получения событий'),
                description=I18nString(
                    'Интервал между запросами к FunPay на получение событий.\n'
                    'Чем меньше интервал, тем быстрее FunPay Hub получает информацию о новых '
                    'сообщениях / заказах и т.д.\n\n',
                ),
                default_value=5.0,
                metadata={'emoji': '⏳'},
            ),
        )
