from __future__ import annotations


__all__ = ['GeneralProperties']

from funpayhub.lib.properties import Properties, FloatParameter, ChoiceParameter, StringParameter
from funpayhub.app.properties.flags import ParameterFlags
from funpayhub.lib.properties.parameter.choice_parameter import Choice
from .validators import proxy_validator


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

        self.proxy = self.attach_parameter(
            StringParameter(
                id='proxy',
                name='$props.general.proxy:name',
                description='$props.general.proxy:description',
                default_value='',
                flags=[ParameterFlags.HIDE_VALUE],
                validator=proxy_validator
            ),
        )

        self.user_agent = self.attach_parameter(
            StringParameter(
                id='user_agent',
                name='$props.general.user_agent:name',
                description='$props.general.user_agent:description',
                default_value='',
            ),
        )

        self.golden_key = self.attach_parameter(
            StringParameter(
                id='golden_key',
                name='$props.general.golden_key:name',
                description='$props.general.golden_key:description',
                default_value='',
                flags=[ParameterFlags.HIDE_VALUE],
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
