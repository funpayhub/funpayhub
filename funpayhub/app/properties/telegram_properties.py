from __future__ import annotations


__all__ = ['TelegramProperties']


from funpayhub.lib.properties import Properties, IntParameter, StringParameter, ToggleParameter
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
            description='$props.new_message_appearance:description'
        )

        self.show_mine = self.attach_parameter(ToggleParameter(
            id='show_mine',
            name='$props.new_message_appearance.show_mine:name',
            description='$new_message_appearance.show_mine:description',
            default_value=True,
        ))

        self.show_if_mine_only = self.attach_parameter(ToggleParameter(
            id='show_if_mine_only',
            name='$props.new_message_appearance.show_if_mine_only:name',
            description='$new_message_appearance.show_if_mine_only:description',
            default_value=True,
        ))

        self.show_by_bot = self.attach_parameter(ToggleParameter(
            id='show_by_bot',
            name='$props.new_message_appearance.show_by_bot:name',
            description='$new_message_appearance.show_by_bot:description',
            default_value=True,
        ))

        self.show_by_bot_only = self.attach_parameter(ToggleParameter(
            id='show_by_bot_only',
            name='$props.new_message_appearance.show_by_bot_only:name',
            description='$new_message_appearance.show_by_bot_only:description',
            default_value=True,
        ))

        self.show_through_bot = self.attach_parameter(ToggleParameter(
            id='show_through_bot',
            name='$props.new_message_appearance.show_through_bot:name',
            description='$new_message_appearance.show_through_bot:description',
            default_value=True,
        ))

        self.show_trough_bot_only = self.attach_parameter(ToggleParameter(
            id='show_trough_bot_only',
            name='$props.new_message_appearance.show_trough_bot_only:name',
            description='$new_message_appearance.show_trough_bot_only:description',
            default_value=True,
        ))

        self.max_templates_on_page = self.attach_parameter(IntParameter(
            id='max_templates_on_page',
            name='$props.new_message_appearance.max_templates_on_page:name',
            description='$new_message_appearance.max_templates_on_page:description',
            default_value=3,
        ))
