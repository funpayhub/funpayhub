from __future__ import annotations

from pyconfigtree import Node, ListParameter
from pyconfigtree.source.toml import TOMLSource
from funpayhub.lib.translater import ru, en
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag

from funpayhub.app.notification_channels import NotificationChannels


class TelegramNotificationsProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'telegram_notifications',
            name=ru('Telegram уведомления'),
            description=en('nodesc'),
            source=TOMLSource('config/telegram_notifications.toml'),
            flags={TelegramUIEmojiFlag('🔔')},
        )

        self.system: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.SYSTEM,
                name=ru('Системные'),
                description=(
                    'Список чатов, подписанных на уведомления о запуске / остановке FunPayHub '
                    'и прочих системных событиях (формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.error: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.ERROR,
                name=ru('Ошибки'),
                description=(
                    'Список чатов, подписанных на уведомления об ошибках в работе FunPayHub '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.offers_raised: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.OFFER_RAISED,
                name=ru('Поднятие лотов'),
                description=(
                    'Список чатов, подписанных на уведомления о поднятии лотов '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.new_message: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.NEW_MESSAGE,
                name=ru('Новое сообщение'),
                description=(
                    'Список чатов, подписанных на уведомления о новых сообщениях '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.new_sale: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.NEW_SALE,
                name=ru('Новый заказ'),
                description=(
                    'Список чатов, подписанных на уведомления о новых заказах '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.sale_status_changed: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.SALE_STATUS_CHANGED,
                name=ru('Изменение статуса заказа'),
                description=(
                    'Список чатов, подписанных на уведомления об изменениях статус заказа '
                    '(завершение, возврат средств, переоткрытие и т.д.) '
                    '(формат: "chat_id.thread_it").',
                ),
                default_factory=list,
            ),
        )

        self.review_1: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.REVIEW_1,
                name=ru('Отзывы с 1 звездой'),
                description=en('nodesc'),
                default_factory=list,
            ),
        )

        self.review_2: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.REVIEW_2,
                name=ru('Отзывы с 2 звездами'),
                description=en('nodesc'),
                default_factory=list,
            ),
        )

        self.review_3: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.REVIEW_3,
                name=ru('Отзывы с 3 звездами'),
                description=en('nodesc'),
                default_factory=list,
            ),
        )

        self.review_4: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.REVIEW_4,
                name=ru('Отзывы с 4 звездами'),
                description=en('nodesc'),
                default_factory=list,
            ),
        )

        self.review_5: ListParameter[str] = self._attach_node(
            ListParameter(
                NotificationChannels.REVIEW_5,
                name=ru('Отзывы с 5 звездами'),
                description=en('nodesc'),
                default_factory=list,
            ),
        )
