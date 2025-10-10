from __future__ import annotations


__all__ = ['GeneralProperties']


from funpayhub.lib.properties import Properties, FloatParameter, ChoiceParameter
from funpayhub.lib.properties.parameter.choice_parameter import Choice


class GeneralProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name='$props.general:name',
            description='$props.general:description',
        )

        self.language = self.attach_parameter(
            ChoiceParameter(
                id='language',
                name='$props.general.language:name',
                description='$props.general.language:description',
                choices=(
                    Choice('ru', '🇷🇺 Русский', 'ru'),
                    Choice('en', '🇬🇧 English', 'en'),
                    Choice('uk', '🇺🇦 Українська', 'uk'),
                    Choice('banana', '🍌 Bacunana', 'banana'),
                ),
                default_value='ru',
            ),
        )

        self.runner_request_interval = self.attach_parameter(
            FloatParameter(
                id='runner_request_interval',
                name='$props.general.runner_request_interval:name',
                description='$props.general.runner_request_interval:description',
                default_value=5.0,
            ),
        )
