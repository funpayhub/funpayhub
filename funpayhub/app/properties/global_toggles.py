from __future__ import annotations
from funpayhub.lib.properties import Properties, ToggleParameter



class TogglesProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='toggles',
            name='$props.toggles:name',
            description='$props.toggles:description',
        )

        self.auto_delivery = self.attach_parameter(
            ToggleParameter(
                properties=self,
                id='auto_delivery',
                name='$props.toggles.auto_delivery:name',
                description='$props.toggles.auto_delivery:description',
                default_value=True,
            ),
        )

        self.auto_restock = self.attach_parameter(
            ToggleParameter(
                properties=self,
                id='auto_restock',
                name='$props.toggles.auto_restock:name',
                description='$props.toggles.auto_restock:description',
                default_value=True,
            )
        )

        self.auto_response = self.attach_parameter(
            ToggleParameter(
                properties=self,
                id='auto_response',
                name='$props.toggles.auto_response:name',
                description='$props.toggles.auto_response:description',
                default_value=True,
            ),
        )

        self.auto_raise = self.attach_parameter(
            ToggleParameter(
                properties=self,
                id='auto_raise',
                name='$props.toggles.auto_raise:name',
                description='$props.toggles.auto_raise:description',
                default_value=True,
            ),
        )