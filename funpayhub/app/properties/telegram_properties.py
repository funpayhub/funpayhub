from __future__ import annotations


__all__ = ['TelegramProperties']


from pyconfigtree import Properties, IntParameter, BoolParameter, ListParameter, StringParameter
from hubplatform.i18n import I18nString
from funpayhub.app.properties.telegram_notifications import TelegramNotificationsProperties


# from .validators import proxy_validator, entries_validator


class TelegramProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='telegram',
            name=I18nString('Настройки Telegram бота'),
            description=I18nString(''),
            metadata={'emoji': '🔷'},
        )

        self.bot = self.attach_node(TelegramBot())
        self.appearance = self.attach_node(TelegramAppearance())
        self.notifications = self.attach_node(TelegramNotificationsProperties())


class TelegramBot(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='bot',
            name=I18nString(
                key='funpayhub.properties.telegram.bot.name',
                fallback='Бот',
            ),
            description=I18nString(''),
            metadata={'emoji': '🔧'},
        )

        self.token = self.attach_node(
            StringParameter(
                node_id='token',
                name=I18nString(
                    key='funpayhub.properties.telegram.bot.token.name',
                    fallback='Токен',
                ),
                description=I18nString(''),
                default_value='',
                metadata={'emoji': '🔑', 'protect_value': True},
            ),
        )

        self.password = self.attach_node(
            StringParameter(
                node_id='password',
                name=I18nString(
                    key='funpayhub.properties.telegram.bot.password.name',
                    fallback='Пароль',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.bot.password.description',
                    fallback='Пароль от Telegram панели управления FunPayHub.',
                ),
                default_value='',
                metadata={'emoji': '🔑', 'protect_value': True},
            ),
        )

        self.authorized_users = self.attach_node(
            ListParameter(
                node_id='authorized_users',
                name=I18nString(
                    key='funpayhub.properties.telegram.bot.authorized_users.name',
                    fallback='Авторизированые пользователи',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.bot.authorized_users.description',
                    fallback='ID пользователей, у которых есть доступ к телеграм боту.',
                ),
                default_factory=list,
                metadata={'emoji': '🔐'},
            ),
        )

        self.proxy = self.attach_node(
            StringParameter(
                node_id='proxy',
                name=I18nString(
                    key='funpayhub.properties.telegram.bot.proxy.name',
                    fallback='Прокси',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.bot.proxy.description',
                    fallback='Прокси для Telegram бота.',
                ),
                # validator=proxy_validator,
                default_value='',
                metadata={'emoji': '🔗', 'protect_value': True},
            ),
        )


class TelegramAppearance(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='appearance',
            name=I18nString('Внешний вид'),
            description=I18nString('Настройки внешнего вида Telegram бота.'),
            metadata={'emoji': '🎨'},
        )

        self.max_menu_blocks = self.attach_node(
            IntParameter(
                node_id='max_menu_blocks',
                name=I18nString(
                    key='funpayhub.properties.telegram.appearance.max_menu_blocks.name',
                    fallback='Кол-во элементов на странице',
                ),
                description=I18nString(
                    key='funpayuhub.properties.telegram.appearance.max_menu_blocks.description',
                    fallback='Максимальное кол-во элементов на 1 странице Telegam меню.\n'
                    'Кнопки навигации не учитываются.',
                ),
                default_value=6,
                # validator=entries_validator,
                metadata={'emoji': '📋'},
            ),
        )

        self.new_message_appearance = self.attach_node(NewMessageNotificationAppearance())


class NewMessageNotificationAppearance(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='new_message_appearance',
            name=I18nString(
                key='funpayhub.properties.telegram.appearance.new_message_notification.name',
                fallback='Вид увед. о новых сообщениях',
            ),
            description=I18nString(
                key='funpayhub.properties.telegram.appearance.new_message_notification.description',
                fallback='Настройки вида Telegram уведомлений о новых сообщениях в чатах FunPay.',
            ),
            metadata={'emoji': '💬'},
        )

        self.show_mine = self.attach_node(
            BoolParameter(
                node_id='show_mine',
                name=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_mine.name',
                    fallback='Отображать мои сообщения',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_mine.description',
                    fallback='Отображать ли сообщения, '
                    'отправленные вами через FunPay (не через FunPay Hub!)',
                ),
                default_value=False,
            ),
        )

        self.show_if_mine_only = self.attach_node(
            BoolParameter(
                node_id='show_if_mine_only',
                name=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_if_mine_only.name',
                    fallback='Увед., если только мои',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_if_mine_only.description',
                    fallback='Присылать ли уведомление о новых сообщениях в чате, '
                    'если все новые сообщения '
                    'отправлены вами через FunPay (не через FunPay Hub!)',
                ),
                default_value=False,
            ),
        )

        self.show_automatic = self.attach_node(
            BoolParameter(
                node_id='show_automatic',
                name=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_automatic.name',
                    fallback='Отображать автоматические',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_automatic.description',
                    fallback='Отображать ли сообщения, отправленные FunPay Hub в автоматическом '
                    'режиме (автовыдача / автоответ / хуки / плагины и т.д.)',
                ),
                default_value=True,
            ),
        )

        self.show_automatic_only = self.attach_node(
            BoolParameter(
                node_id='show_automatic_only',
                name=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_automatic_only.name',
                    fallback='Увед., если только автоматические',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_automatic_only.description',
                    fallback='Присылать ли уведомление о новых сообщениях в чате, если все новые сообщения '
                    'отправлены FunPay Hub в автоматическом режиме '
                    '(автовыдача / автоответ / хуки / плагины и т.д.)',
                ),
                default_value=True,
            ),
        )

        self.show_mine_from_hub = self.attach_node(
            BoolParameter(
                node_id='show_mine_from_hub',
                name=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_mine_from_hub.name',
                    fallback='Отображать мои через Hub',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_mine_from_hub.description',
                    fallback='Отображать ли сообщения, которые были отправлены вами с помощью '
                    'FunPay Hub (через Telegram меню ответа на сообщения и т.д.)',
                ),
                default_value=False,
            ),
        )

        self.show_mine_from_hub_only = self.attach_node(
            BoolParameter(
                node_id='show_mine_from_hub_only',
                name=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_mine_from_hub_only.name',
                    fallback='Увед., если только мои через Hub',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.appearance.new_message_notification'
                    '.show_mine_from_hub_only.description',
                    fallback='Присылать ли уведомление о новых сообщениях в чате, '
                    'если все новые сообщения отправлены вами через Hub '
                    '(через Telegram меню ответа на сообщения и т.д.)',
                ),
                default_value=False,
            ),
        )
