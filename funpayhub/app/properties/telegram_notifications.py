from __future__ import annotations

from funpayhub.lib.properties import Properties, ListParameter

from funpayhub.app.notification_channels import NotificationChannels


class TelegramNotificationsProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='telegram_notifications',
            name='$telegram_notifications:name',
            description='$telegram_notifications:description',
            file='config/telegram_notifications.toml',
        )

        self.system: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.SYSTEM,
                name='$telegram_notifications.system:name',
                description='$telegram_notifications.system:description',
                default_factory=list,
            ),
        )

        self.error: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.ERROR,
                name='$telegram_notifications.error:name',
                description='$telegram_notifications.error:description',
                default_factory=list,
            ),
        )

        self.offers_raised: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.OFFER_RAISED,
                name='$telegram_notifications.offers_raised:name',
                description='$telegram_notifications.offers_raised:description',
                default_factory=list,
            ),
        )

        self.new_message: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.NEW_MESSAGE,
                name='$telegram_notifications.new_message:name',
                description='$telegram_notifications.new_message:description',
                default_factory=list,
            ),
        )

        self.new_sale: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.NEW_SALE,
                name='$telegram_notifications.new_sale:name',
                description='$telegram_notifications.new_sale:description',
                default_factory=list,
            ),
        )

        self.sale_status_changed: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.SALE_STATUS_CHANGED,
                name='$telegram_notifications.sale_status_changed:name',
                description='$telegram_notifications.sale_status_changed:description',
                default_factory=list,
            ),
        )

        self.review_1: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_1,
                name='$telegram_notifications.review_1:name',
                description='$telegram_notifications.review_1:description',
                default_factory=list,
            ),
        )

        self.review_2: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_2,
                name='$telegram_notifications.review_2:name',
                description='$telegram_notifications.review_2:description',
                default_factory=list,
            ),
        )

        self.review_3: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_3,
                name='$telegram_notifications.review_3:name',
                description='$telegram_notifications.review_3:description',
                default_factory=list,
            ),
        )

        self.review_4: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_4,
                name='$telegram_notifications.review_4:name',
                description='$telegram_notifications.review_4:description',
                default_factory=list,
            ),
        )

        self.review_5: ListParameter[str] = self.attach_node(
            ListParameter(
                id=NotificationChannels.REVIEW_5,
                name='$telegram_notifications.review_5:name',
                description='$telegram_notifications.review_5:description',
                default_factory=list,
            ),
        )
