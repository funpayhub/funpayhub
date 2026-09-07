from __future__ import annotations

from pyconfigtree import Properties, ListParameter
from hubplatform.i18n import I18nString
from pyconfigtree.source.toml import TOMLSource

# from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag
from funpayhub.app.notification_channels import NotificationChannels


class TelegramNotificationsProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='telegram_notifications',
            name=I18nString(
                key='funpayhub.properties.telegram.notifications.name',
                fallback='Telegram уведомления',
            ),
            description=I18nString(''),
            source=TOMLSource('config/telegram_notifications.toml'),
            # flags={TelegramUIEmojiFlag('🔔')},
        )

        self.system: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.SYSTEM,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.system.name',
                    fallback='Системные',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.notifications.system.description',
                    fallback='Список чатов, подписанных на уведомления о запуске / остановке '
                    'FunPayHub и прочих системных событиях (формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.error: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.ERROR,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.errors.name',
                    fallback='Ошибки',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.notifications.errors.description',
                    fallback='Список чатов, подписанных на уведомления об ошибках в работе FunPayHub '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.offers_raised: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.OFFER_RAISED,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.offers_raised.name',
                    fallback='Поднятие лотов',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.notifications.offers_raised.description',
                    fallback='Список чатов, подписанных на уведомления о поднятии лотов '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.new_message: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.NEW_MESSAGE,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.new_message.name',
                    fallback='Новое сообщение',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.notifications.new_message.description',
                    fallback='Список чатов, подписанных на уведомления о новых сообщениях '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.new_sale: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.NEW_SALE,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.new_sale.name',
                    fallback='Новый заказ',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.notifications.new_sale.description',
                    fallback='Список чатов, подписанных на уведомления о новых заказах '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.sale_status_changed: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.SALE_STATUS_CHANGED,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.sale_status_changed.name',
                    fallback='Изменение статуса заказа',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.notifications.sale_status_changed'
                    '.description',
                    fallback='Список чатов, подписанных на уведомления об изменениях статус заказа '
                    '(завершение, возврат средств, переоткрытие и т.д.) '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.review_1: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.REVIEW_1,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.review_1.name',
                    fallback='Отзывы с 1 звездой',
                ),
                description=I18nString(''),
                default_factory=list,
            ),
        )

        self.review_2: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.REVIEW_2,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.review_2.name',
                    fallback='Отзывы с 2 звездами',
                ),
                description=I18nString(''),
                default_factory=list,
            ),
        )

        self.review_3: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.REVIEW_3,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.review_3.name',
                    fallback='Отзывы с 3 звездами',
                ),
                description=I18nString(''),
                default_factory=list,
            ),
        )

        self.review_4: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.REVIEW_4,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.review_4.name',
                    fallback='Отзывы с 4 звездами',
                ),
                description=I18nString(''),
                default_factory=list,
            ),
        )

        self.review_5: ListParameter[str] = self.attach_node(
            ListParameter(
                node_id=NotificationChannels.REVIEW_5,
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.review_5.name',
                    fallback='Отзывы с 5 звездами',
                ),
                description=I18nString(''),
                default_factory=list,
            ),
        )
