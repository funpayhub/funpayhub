from __future__ import annotations

__all__ = ['TelegramProperties',]


from funpayhub.properties import Properties, ToggleParameter, StringParameter, IntParameter


class TelegramProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='telegram',
            name='$props_telegram:name',
            description='$props_telegram:description'
        )

        self.general = self.attach_properties(TelegramGeneral())
        self.appearance = self.attach_properties(TelegramAppearance())


class TelegramGeneral(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name='$props_telegram.general:name',
            description='$props_telegram.general:description'
        )

        self.token = self.attach_parameter(
            StringParameter(
                properties=self,
                id='token',
                name='$props_telegram.general.token:name',
                description='$props_telegram.general.token:description',
                default_value='',
            )
        )

        self.password = self.attach_parameter(
            StringParameter(
                properties=self,
                id='password',
                name='$props_telegram.general.password:name',
                description='$props_telegram.general.password:description',
                default_value='',
            )
        )


class TelegramAppearance(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='appearance',
            name='$props_telegram.appearance:name',
            description='$props_telegram.appearance:description'
        )

        self.show_emoji = self.attach_parameter(
            ToggleParameter(
                properties=self,
                id='show_emoji',
                name='$props_telegram.appearance.show_emoji:name',
                description='$props_telegram.appearance.show_emoji:description',
                default_value=True
            )
        )

        self.menu_entries_amount = self.attach_parameter(
            IntParameter(
                properties=self,
                id='menu_entries_amount',
                name='$props_telegram.appearance.menu_entries_amount:name',
                description='$props_telegram.appearance.menu_entries_amount:description',
                default_value=6
            )
        )
