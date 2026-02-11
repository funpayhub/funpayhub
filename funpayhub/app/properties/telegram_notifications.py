from __future__ import annotations

from funpayhub.lib.properties import Properties, ListParameter
from funpayhub.lib.translater import _

from funpayhub.app.notification_channels import NotificationChannels


class TelegramNotificationsProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='telegram_notifications',
            name=_('🔔 Telegram уведомления'),
            description=_('nodesc'),
            file='config/telegram_notifications.toml',
        )

        self.system: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.SYSTEM,
                name=_('Системные'),
                description=_(
                    'Список чатов, подписанных на уведомления о запуске / остановке FunPayHub и прочих системных событиях (формат: "chat_id.thread_it").'
                ),
                default_factory=list,
            ),
        )

        self.error: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.ERROR,
                name=_('Ошибки'),
                description=_(
                    'Список чатов, подписанных на уведомления об ошибках в работе FunPayHub (формат: "chat_id.thread_it").'
                ),
                default_factory=list,
            ),
        )

        self.offers_raised: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.OFFER_RAISED,
                name=_('Поднятие лотов'),
                description=_(
                    'Список чатов, подписанных на уведомления о поднятии лотов (формат: "chat_id.thread_it").'
                ),
                default_factory=list,
            ),
        )

        self.new_message: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.NEW_MESSAGE,
                name=_('Новое сообщение'),
                description=_(
                    'Список чатов, подписанных на уведомления о новых сообщениях (формат: "chat_id.thread_it").'
                ),
                default_factory=list,
            ),
        )

        self.new_sale: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.NEW_SALE,
                name=_('Новый заказ'),
                description=_(
                    'Список чатов, подписанных на уведомления о новых заказах (формат: "chat_id.thread_it").'
                ),
                default_factory=list,
            ),
        )

        self.sale_status_changed: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.SALE_STATUS_CHANGED,
                name=_('Изменение статуса заказа'),
                description=_(
                    'Список чатов, подписанных на уведомления об изменениях статус заказа (завершение, возврат средств, переоткрытие и т.д.) (формат: "chat_id.thread_it").'
                ),
                default_factory=list,
            ),
        )

        self.review_1: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_1,
                name=_('Отзывы с 1 звездой'),
                description=_('nodesc'),
                default_factory=list,
            ),
        )

        self.review_2: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_2,
                name=_('Отзывы с 2 звездами'),
                description=_('nodesc'),
                default_factory=list,
            ),
        )

        self.review_3: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_3,
                name=_('Отзывы с 3 звездами'),
                description=_('nodesc'),
                default_factory=list,
            ),
        )

        self.review_4: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_4,
                name=_('Отзывы с 4 звездами'),
                description=_('nodesc'),
                default_factory=list,
            ),
        )

        self.review_5: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_5,
                name=_('Отзывы с 5 звездами'),
                description=_('nodesc'),
                default_factory=list,
            ),
        )
