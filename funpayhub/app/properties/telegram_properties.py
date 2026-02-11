from __future__ import annotations

from funpayhub.lib.translater import _


__all__ = ['TelegramProperties']


from funpayhub.lib.properties import (
    Properties,
    IntParameter,
    ListParameter,
    StringParameter,
    ToggleParameter,
)

from funpayhub.app.properties.flags import ParameterFlags as ParamFlags
from funpayhub.app.properties.telegram_notifications import TelegramNotificationsProperties

from .validators import entries_validator
from ...lib.base_app.properties_flags import TelegramUIEmojiFlag


class TelegramProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='telegram',
            name=_('Настройки Telegram бота'),
            description=_('nodesc'),
            flags=[TelegramUIEmojiFlag('🔷')],
        )

        self.general = self.attach_node(TelegramGeneral())
        self.appearance = self.attach_node(TelegramAppearance())
        self.notifications = self.attach_node(TelegramNotificationsProperties())


class TelegramGeneral(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name=_('Общие'),
            description=_('nodesc'),
            flags=[TelegramUIEmojiFlag('🔧')],
        )

        self.token = self.attach_node(
            StringParameter(
                id='token',
                name=_('Токен'),
                description=_('nodesc'),
                default_value='',
                flags=[TelegramUIEmojiFlag('🔑')],
            ),
        )

        self.password = self.attach_node(
            StringParameter(
                id='password',
                name=_('Пароль'),
                description=_('Пароль от Telegram панели управления FunPayHub.'),
                default_value='',
                flags=[ParamFlags.PROTECT_VALUE, TelegramUIEmojiFlag('🔑')],
            ),
        )

        self.authorized_users = self.attach_node(
            ListParameter(
                id='authorized_users',
                name=_('Авторизированые пользователи'),
                description=_('ID пользователей, у которых есть доступ к телеграм боту.'),
                default_factory=list,
                flags=[TelegramUIEmojiFlag('🔐')],
            ),
        )


class TelegramAppearance(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='appearance',
            name=_('Внешний вид'),
            description=_('Настройки внешнего вида Telegram бота.'),
            flags=[TelegramUIEmojiFlag('🎨')],
        )

        self.max_menu_lines = self.attach_node(
            IntParameter(
                id='max_menu_lines',
                name=_('Кол-во элементов на странице'),
                description=_(
                    'Максимальное кол-во элементов на 1 странице Telegam меню.\n'
                    'Кнопки навигации не учитываются.',
                ),
                default_value=6,
                validator=entries_validator,
                flags=[TelegramUIEmojiFlag('📋')],
            ),
        )

        self.new_message_appearance = self.attach_node(NewMessageNotificationAppearance())


class NewMessageNotificationAppearance(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='new_message_appearance',
            name=_('Вид увед. о новых сообщениях'),
            description=_(
                'Настройки вида Telegram уведомлений о новых сообщениях в чатах FunPay.',
            ),
            flags=[TelegramUIEmojiFlag('💬')],
        )

        self.show_mine = self.attach_node(
            ToggleParameter(
                id='show_mine',
                name=_('Отображать мои'),
                description=_(
                    'Отображать ли сообщения, отправленные вами через FunPay (не через FunPay Hub!)',
                ),
                default_value=False,
            ),
        )

        self.show_if_mine_only = self.attach_node(
            ToggleParameter(
                id='show_if_mine_only',
                name=_('Увед., если только мои'),
                description=_(
                    'Присылать ли уведомление о новых сообщениях в чате, если все новые сообщения '
                    'отправлены вами через FunPay (не через FunPay Hub!)',
                ),
                default_value=False,
            ),
        )

        self.show_automatic = self.attach_node(
            ToggleParameter(
                id='show_automatic',
                name=_('Отображать автоматические'),
                description=_(
                    'Отображать ли сообщения, отправленные FunPay Hub в автоматическом режиме '
                    '(автовыдача / автоответ / хуки / плагины и т.д.)',
                ),
                default_value=True,
            ),
        )

        self.show_automatic_only = self.attach_node(
            ToggleParameter(
                id='show_automatic_only',
                name=_('Увед., если только автоматические'),
                description=_(
                    'Присылать ли уведомление о новых сообщениях в чате, если все новые сообщения '
                    'отправлены FunPay Hub в автоматическом режиме '
                    '(автовыдача / автоответ / хуки / плагины и т.д.)',
                ),
                default_value=True,
            ),
        )

        self.show_mine_from_hub = self.attach_node(
            ToggleParameter(
                id='show_mine_from_hub',
                name=_('Отображать мои через Hub'),
                description=_(
                    'Отображать ли сообщения, которые были отправлены вами с помощью FunPay Hub '
                    '(через Telegram меню ответа на сообщения и т.д.)',
                ),
                default_value=False,
            ),
        )

        self.show_mine_from_hub_only = self.attach_node(
            ToggleParameter(
                id='show_mine_from_hub_only',
                name=_('Увед., если только мои через Hub'),
                description=_(
                    'Присылать ли уведомление о новых сообщениях в чате, если все новые сообщения '
                    'отправлены вами через Hub (через Telegram меню ответа на сообщения и т.д.)',
                ),
                default_value=False,
            ),
        )
