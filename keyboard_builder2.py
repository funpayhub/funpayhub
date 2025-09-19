from dataclasses import dataclass
import funpayhub.lib.properties.parameter as p


@dataclass
class InPlaceButton:
    text:  str

@dataclass
class Button:
    text: str


@dataclass
class Menu:
    buttons: list[Button]


class DefaultPropertiesBuilders:
    builders = {
        p.ToggleParameter: InPlaceButton('some_text'),
        p.IntParameter: Button('some_text'),
        p.FloatParameter: Button('some_text'),
        p.StringParameter: Button('some_text'),
        p.ListParameter: Menu([]),
        p.ChoiceParameter: Menu([])
    }
