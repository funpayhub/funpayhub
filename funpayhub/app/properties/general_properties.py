from __future__ import annotations

__all__ = ['GeneralProperties',]


from funpayhub.lib.properties import Properties, ChoiceParameter
from funpayhub.lib.properties.parameter.choice_parameter import Item


class GeneralProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name='$props.general:name',
            description='$props.general:description'
        )

        self.language = ChoiceParameter(
            properties=self,
            id='language',
            name='$props.general.language:name',
            description='$props.general.language:description',
            choices=(
                Item('$lang_russian', 'ru'),
                Item('$lang_english', 'en')
            ),
            default_value=0,
        )
