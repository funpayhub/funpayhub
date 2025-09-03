from __future__ import annotations


__all__ = ['GeneralProperties']


from funpayhub.lib.properties import Properties, ChoiceParameter, FloatParameter
from funpayhub.lib.properties.parameter.choice_parameter import Item


class GeneralProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name='$props.general:name',
            description='$props.general:description',
        )

        self.language = self.attach_parameter(
            ChoiceParameter(
                properties=self,
                id='language',
                name='$props.general.language:name',
                description='$props.general.language:description',
                choices=(
                    Item('🇷🇺 Русский', 'ru'),
                    Item('🇬🇧 English', 'en'),
                    Item('🇺🇦 Українська', 'uk'),
                    Item('🍌 Bacunana', 'banana'),
                ),
                default_value=0,
            ),
        )

        self.runner_request_interval = self.attach_parameter(
            FloatParameter(
                properties=self,
                id='runner_request_interval',
                name='$props.general.runner_request_interval:name',
                description='$props.general.runner_request_interval:description',
                default_value=5.0
            )
        )

