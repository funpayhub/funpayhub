from __future__ import annotations

from funpayhub.lib.properties import Properties, ListParameter


class TelegramNotificationsProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='telegram_notifications',
            name='$telegram_notifications:name',
            description='$telegram_notifications:description',
            file='config/telegram_notifications.toml',
        )

        self.system: ListParameter[str] = self.attach_parameter(
            ListParameter(
                id='hub_life',
                name='$telegram_notifications.system:name',
                description='$telegram_notifications.system:description',
                default_value=[],
            ),
        )

        self.error: ListParameter[str] = self.attach_parameter(
            ListParameter(
                id='error',
                name='$telegram_notifications.error:name',
                description='$telegram_notifications.error:description',
                default_value=[],
            )
        )

        self.lots_raised: ListParameter[str] = self.attach_parameter(
            ListParameter(
                id='lots_raised',
                name='$telegram_notifications.lots_raised:name',
                description='$telegram_notifications.lots_raised:description',
                default_value=[],
            )
        )

        self.new_message: ListParameter[str] = self.attach_parameter(
            ListParameter(
                id='new_message',
                name='$telegram_notifications.new_message:name',
                description='$telegram_notifications.new_message:description',
                default_value=[],
            ),
        )

        self.new_sale: ListParameter[str] = self.attach_parameter(
            ListParameter(
                id='new_sale',
                name='$telegram_notifications.new_sale:name',
                description='$telegram_notifications.new_sale:description',
                default_value=[],
            ),
        )

        self.sale_status_changed: ListParameter[str] = self.attach_parameter(
            ListParameter(
                id='sale_status_changed',
                name='$telegram_notifications.sale_status_changed:name',
                description='$telegram_notifications.sale_status_changed:description',
                default_value=[],
            )
        )

        self.review: ListParameter[str] = self.attach_parameter(
            ListParameter(
                id='review',
                name='$telegram_notifications.review:name',
                description='$telegram_notifications.review:description',
                default_value=[],
            ),
        )
