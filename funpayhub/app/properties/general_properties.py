from __future__ import annotations

__all__ = ['GeneralProperties',]


from funpayhub.properties import Properties, ChoiceParameter
from funpayhub.properties.parameter.choice_parameter import Item


class GeneralProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name='$props_general:name',
            description='$props_general:description'
        )

        self.language = ChoiceParameter(
            properties=self,
            id='language',
            name='$props_general.language:name',
            description='$props_general.language:description',
            choices=(
                Item('$lang_russian', 'ru'),
                Item('$lang_english', 'en')
            ),
            default_value=0,
        )
