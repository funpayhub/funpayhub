from __future__ import annotations

from funpayhub.lib.translater import ru, en


__all__ = ['TelegramProperties']


from pyconfigtree import Node, IntParameter, ListParameter, StringParameter, BoolParameter

from funpayhub.app.properties.flags import ParameterFlags as ParamFlags
from funpayhub.app.properties.telegram_notifications import TelegramNotificationsProperties

from .validators import proxy_validator, entries_validator
from ...lib.base_app.properties_flags import TelegramUIEmojiFlag


class TelegramProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'telegram',
            name=ru('Настройки Telegram бота'),
            description=en('nodesc'),
            flags={TelegramUIEmojiFlag('🔷')},
        )

        self.general = self._attach_node(TelegramGeneral())
        self.appearance = self._attach_node(TelegramAppearance())
        self.notifications = self._attach_node(TelegramNotificationsProperties())


class TelegramGeneral(Node):
    def __init__(self) -> None:
        super().__init__(
            'general',
            name=ru('Общие'),
            description=en('nodesc'),
            flags={TelegramUIEmojiFlag('🔧')},
        )

        self.token = self._attach_node(
            StringParameter(
                'token',
                name=ru('Токен'),
                description=en('nodesc'),
                default_value='',
                flags={ParamFlags.PROTECT_VALUE, TelegramUIEmojiFlag('🔑')},
            ),
        )

        self.password = self._attach_node(
            StringParameter(
                'password',
                name=ru('Пароль'),
                description=ru('Пароль от Telegram панели управления FunPayHub.'),
                default_value='',
                flags={ParamFlags.PROTECT_VALUE, TelegramUIEmojiFlag('🔑')},
            ),
        )

        self.authorized_users = self._attach_node(
            ListParameter(
                'authorized_users',
                name=ru('Авторизированые пользователи'),
                description=ru('ID пользователей, у которых есть доступ к телеграм боту.'),
                default_factory=list,
                flags={TelegramUIEmojiFlag('🔐')},
            ),
        )

        self.proxy = self._attach_node(
            StringParameter(
                'proxy',
                name=ru('Прокси'),
                description=ru('Прокси для Telegram бота.'),
                validator=proxy_validator,
                default_value='',
                flags={TelegramUIEmojiFlag('🔗'), ParamFlags.PROTECT_VALUE},
            ),
        )


class TelegramAppearance(Node):
    def __init__(self) -> None:
        super().__init__(
            'appearance',
            name=ru('Внешний вид'),
            description=ru('Настройки внешнего вида Telegram бота.'),
            flags={TelegramUIEmojiFlag('🎨')},
        )

        self.max_menu_lines = self._attach_node(
            IntParameter(
                'max_menu_lines',
                name=ru('Кол-во элементов на странице'),
                description=(
                    'Максимальное кол-во элементов на 1 странице Telegam меню.\n'
                    'Кнопки навигации не учитываются.',
                ),
                default_value=6,
                validator=entries_validator,
                flags={TelegramUIEmojiFlag('📋')},
            ),
        )

        self.new_message_appearance = self._attach_node(NewMessageNotificationAppearance())


class NewMessageNotificationAppearance(Node):
    def __init__(self) -> None:
        super().__init__(
            'new_message_appearance',
            name=ru('Вид увед. о новых сообщениях'),
            description=ru(
                'Настройки вида Telegram уведомлений о новых сообщениях в чатах FunPay.',
            ),
            flags={TelegramUIEmojiFlag('💬')},
        )

        self.show_mine = self._attach_node(
            BoolParameter(
                'show_mine',
                name=ru('Отображать мои'),
                description=(
                    'Отображать ли сообщения, отправленные вами через FunPay (не через FunPay Hub!)',
                ),
                default_value=False,
            ),
        )

        self.show_if_mine_only = self._attach_node(
            BoolParameter(
                'show_if_mine_only',
                name=ru('Увед., если только мои'),
                description=(
                    'Присылать ли уведомление о новых сообщениях в чате, если все новые сообщения '
                    'отправлены вами через FunPay (не через FunPay Hub!)',
                ),
                default_value=False,
            ),
        )

        self.show_automatic = self._attach_node(
            BoolParameter(
                'show_automatic',
                name=ru('Отображать автоматические'),
                description=(
                    'Отображать ли сообщения, отправленные FunPay Hub в автоматическом режиме '
                    '(автовыдача / автоответ / хуки / плагины и т.д.)',
                ),
                default_value=True,
            ),
        )

        self.show_automatic_only = self._attach_node(
            BoolParameter(
                'show_automatic_only',
                name=ru('Увед., если только автоматические'),
                description=(
                    'Присылать ли уведомление о новых сообщениях в чате, если все новые сообщения '
                    'отправлены FunPay Hub в автоматическом режиме '
                    '(автовыдача / автоответ / хуки / плагины и т.д.)',
                ),
                default_value=True,
            ),
        )

        self.show_mine_from_hub = self._attach_node(
            BoolParameter(
                'show_mine_from_hub',
                name=ru('Отображать мои через Hub'),
                description=(
                    'Отображать ли сообщения, которые были отправлены вами с помощью FunPay Hub '
                    '(через Telegram меню ответа на сообщения и т.д.)',
                ),
                default_value=False,
            ),
        )

        self.show_mine_from_hub_only = self._attach_node(
            BoolParameter(
                'show_mine_from_hub_only',
                name=ru('Увед., если только мои через Hub'),
                description=(
                    'Присылать ли уведомление о новых сообщениях в чате, если все новые сообщения '
                    'отправлены вами через Hub (через Telegram меню ответа на сообщения и т.д.)',
                ),
                default_value=False,
            ),
        )
