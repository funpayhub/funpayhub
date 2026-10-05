from __future__ import annotations


__all__ = [
    'FunPayNotificationsCategory',
]

from hubplatform.i18n import I18nString

from funpayhub.app.components.telegram_component.properties.telegram_notifications import (
    NotificationsChannel,
    NotificationsCategory,
)


class FunPayNotificationsCategory(NotificationsCategory):
    def __init__(self) -> None:
        super().__init__(
            node_id='funpay',
            name=I18nString('FunPay'),
            description=I18nString(''),
        )

        self.offer_raised = self.attach_node(
            NotificationsChannel(
                channel_id='offer_raised',
                name=I18nString('Поднятие лотов'),
                description=I18nString(''),
            ),
        )

        self.new_message = self.attach_node(
            NotificationsChannel(
                channel_id='new_message',
                name=I18nString('Новое сообщение'),
                description=I18nString(
                    'Список чатов, подписанных на уведомления о новых сообщениях '
                    '(формат: "chat_id.thread_it").',
                ),
            ),
        )

        self.new_sale = self.attach_node(
            NotificationsChannel(
                channel_id='new_sale',
                name=I18nString('Новый заказ'),
                description=I18nString(
                    'Список чатов, подписанных на уведомления о новых заказах '
                    '(формат: "chat_id.thread_it").',
                ),
            ),
        )

        self.sale_status_changed = self.attach_node(
            NotificationsChannel(
                channel_id='sale_status_changed',
                name=I18nString('Изменение статуса заказа'),
                description=I18nString(
                    'Список чатов, подписанных на уведомления об изменениях статус заказа '
                    '(завершение, возврат средств, переоткрытие и т.д.) '
                    '(формат: "chat_id.thread_it").',
                ),
            ),
        )

        self.review_1 = self.attach_node(
            NotificationsChannel(
                channel_id='review_1',
                name=I18nString('Отзывы с 1 звездой'),
                description=I18nString('nodesc'),
            ),
        )

        self.review_2 = self.attach_node(
            NotificationsChannel(
                channel_id='review_2',
                name=I18nString('Отзывы с 2 звездами'),
                description=I18nString('nodesc'),
            ),
        )

        self.review_3 = self.attach_node(
            NotificationsChannel(
                channel_id='review_3',
                name=I18nString('Отзывы с 3 звездами'),
                description=I18nString('nodesc'),
            ),
        )

        self.review_4 = self.attach_node(
            NotificationsChannel(
                channel_id='review_4',
                name=I18nString('Отзывы с 4 звездами'),
                description=I18nString('nodesc'),
            ),
        )

        self.review_5 = self.attach_node(
            NotificationsChannel(
                channel_id='review_5',
                name=I18nString('Отзывы с 5 звездами'),
                description=I18nString('nodesc'),
            ),
        )
