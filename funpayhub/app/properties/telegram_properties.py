from __future__ import annotations


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


class TelegramProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='telegram',
            name='$props.telegram:name',
            description='$props.telegram:description',
        )

        self.general = self.attach_properties(TelegramGeneral())
        self.appearance = self.attach_properties(TelegramAppearance())
        self.notifications = self.attach_properties(TelegramNotificationsProperties())


class TelegramGeneral(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name='$props.telegram.general:name',
            description='$props.telegram.general:description',
        )

        self.token = self.attach_parameter(
            StringParameter(
                id='token',
                name='$props.telegram.general.token:name',
                description='$props.telegram.general.token:description',
                default_value='',
            ),
        )

        self.password = self.attach_parameter(
            StringParameter(
                id='password',
                name='$props.telegram.general.password:name',
                description='$props.telegram.general.password:description',
                default_value='',
                flags=[ParamFlags.PROTECT_VALUE],
            ),
        )

        self.authorized_users = self.attach_parameter(
            ListParameter(
                id='authorized_users',
                name='$props.telegram.general.authorized_users:name',
                description='$props.telegram.general.authorized_users:description',
                default_factory=list,
            ),
        )


class TelegramAppearance(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='appearance',
            name='$props.telegram.appearance:name',
            description='$props.telegram.appearance:description',
        )

        self.menu_entries_amount = self.attach_parameter(
            IntParameter(
                id='menu_entries_amount',
                name='$props.telegram.appearance.menu_entries_amount:name',
                description='$props.telegram.appearance.menu_entries_amount:description',
                default_value=6,
                validator=entries_validator,
            ),
        )

        self.new_message_appearance = self.attach_properties(NewMessageNotificationAppearance())


class NewMessageNotificationAppearance(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='new_message_appearance',
            name='$props.new_message_appearance:name',
            description='$props.new_message_appearance:description',
        )

        self.show_mine = self.attach_parameter(
            ToggleParameter(
                id='show_mine',
                name='$props.new_message_appearance.show_mine:name',
                description='$props.new_message_appearance.show_mine:description',
                default_value=False,
            ),
        )

        self.show_if_mine_only = self.attach_parameter(
            ToggleParameter(
                id='show_if_mine_only',
                name='$props.new_message_appearance.show_if_mine_only:name',
                description='$props.new_message_appearance.show_if_mine_only:description',
                default_value=False,
            ),
        )

        self.show_automatic = self.attach_parameter(
            ToggleParameter(
                id='show_automatic',
                name='$props.new_message_appearance.show_automatic:name',
                description='$props.new_message_appearance.show_automatic:description',
                default_value=True,
            ),
        )

        self.show_automatic_only = self.attach_parameter(
            ToggleParameter(
                id='show_automatic_only',
                name='$props.new_message_appearance.show_automatic_only:name',
                description='$props.new_message_appearance.show_automatic_only:description',
                default_value=True,
            ),
        )

        self.show_mine_from_hub = self.attach_parameter(
            ToggleParameter(
                id='show_mine_from_hub',
                name='$props.new_message_appearance.show_mine_from_hub:name',
                description='$props.new_message_appearance.show_mine_from_hub:description',
                default_value=False,
            ),
        )

        self.show_mine_from_hub_only = self.attach_parameter(
            ToggleParameter(
                id='show_mine_from_hub_only',
                name='$props.new_message_appearance.show_mine_from_hub_only:name',
                description='$props.new_message_appearance.show_mine_from_hub_only:description',
                default_value=False,
            ),
        )
