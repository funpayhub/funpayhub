from funpayhub.lib.properties import Properties, ListParameter


class TelegramNotificationsProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='telegram_notifications',
            name='$telegram_notifications:name',
            description='$telegram_notifications:description',
            file='config/telegram_notifications.toml'
        )

        self.attach_parameter(
            ListParameter(
                id='new_message',
                name='$telegram_notifications.new_message:name',
                description='$telegram_notifications.new_message:description',
                default_value=[],
            )
        )

        self.attach_parameter(
            ListParameter(
                id='new_order',
                name='$telegram_notifications.new_order:name',
                description='$telegram_notifications.new_order:description',
                default_value=[],
            )
        )

        self.attach_parameter(
            ListParameter(
                id='new_review',
                name='$telegram_notifications.new_review:name',
                description='$telegram_notifications.new_review:description',
                default_value=[],
            )
        )
