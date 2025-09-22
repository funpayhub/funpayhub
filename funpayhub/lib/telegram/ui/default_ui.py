from __future__ import annotations


__all__ = [
    'TOGGLE_UI',
    'MANUAL_CHANGE_PARAM_UI',
    'PROPERTIES_UI',
]


from .types import PropertiesUIBuilder, OneStepPropertiesUIBuilder
from .default_builders import (
    build_parameter_button,
    properties_menu_builder,
    build_parameter_change_menu,
    build_toggle_parameter_button,
    build_long_value_parameter_button,
)


TOGGLE_UI = OneStepPropertiesUIBuilder(
    button_builder=build_toggle_parameter_button,
)

MANUAL_CHANGE_PARAM_UI = PropertiesUIBuilder(
    button_builder=build_parameter_button,
    next_menu=build_parameter_change_menu,
)

PROPERTIES_UI = PropertiesUIBuilder(
    button_builder=build_long_value_parameter_button,
    next_menu=properties_menu_builder,
)
