from __future__ import annotations

from funpayhub.lib.translater import _


__all__ = ['GeneralProperties']

from funpayhub.lib.properties import Properties, FloatParameter, ChoiceParameter, StringParameter
from funpayhub.lib.properties.parameter.choice_parameter import Choice

from funpayhub.app.properties.flags import ParameterFlags

from .validators import proxy_validator


class GeneralProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name=_('🔧 Общие'),
            description=_('nodesc'),
        )

        self.language = self.attach_node(
            ChoiceParameter(
                id='language',
                name=_('🌎 Язык'),
                description=_('nodesc'),
                choices=(
                    Choice('ru', '🇷🇺 Русский', 'ru'),
                    Choice('en', '🇬🇧 English', 'en'),
                    Choice('ua', '🇺🇦 Українська', 'ua'),
                    Choice('banana', '🍌 Bacunana', 'banana'),
                ),
                default_value='ru',
            ),
        )

        self.proxy = self.attach_node(
            StringParameter(
                id='proxy',
                name=_('🌐 Прокси'),
                description=_(
                    'Позволяет скрыть ваш IP-адрес при работе с FunPay.\nИспользуется только для запросов к FunPay, на остальной трафик не влияет.\nПоддерживаются прокси HTTP(S) и SOCKS5.\n'
                ),
                default_value='',
                flags=[ParameterFlags.PROTECT_VALUE],
                validator=proxy_validator,
            ),
        )

        self.user_agent = self.attach_node(
            StringParameter(
                id='user_agent',
                name=_('🌐 User Agent'),
                description=_(
                    'Строка, которая сообщает FunPay, какой браузер и устройство используются.\nПомогает избежать лишних проверок и блокировок.\nИспользуйте User Agent бразуера, из которого вы взяли golden key.'
                ),
                flags=[ParameterFlags.PROTECT_VALUE],
                default_value='',
            ),
        )

        self.golden_key = self.attach_node(
            StringParameter(
                id='golden_key',
                name=_('🔑 Golden Key (токен)'),
                description=_(
                    'Ключ доступа к вашему аккаунту FunPay.\nНужен для работы бота и выполнения запросов от вашего имени.'
                ),
                default_value='',
                flags=[ParameterFlags.PROTECT_VALUE],
            ),
        )

        self.runner_request_interval = self.attach_node(
            FloatParameter(
                id='runner_request_interval',
                name=_('⏱️ Интервал получения событий'),
                description=_(
                    'Интервал между запросами к FunPay на получение событий.\nЧем меньше интервал, тем быстрее FunPay Hub получает информацию о новых сообщениях / заказах и т.д.\n\n'
                ),
                default_value=5.0,
            ),
        )
