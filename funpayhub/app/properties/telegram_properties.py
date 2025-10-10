from __future__ import annotations


__all__ = ['TelegramProperties']


from funpayhub.lib.properties import Properties, IntParameter, StringParameter
from funpayhub.app.properties.flags import ParameterFlags as ParamFlags

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
                flags=[ParamFlags.PROTECT_VALUE]
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
