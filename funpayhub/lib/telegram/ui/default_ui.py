from __future__ import annotations


__all__ = [
    'TOGGLE_BTN',

    'INT_PARAM_BTN',
    'INT_PARAM_MENU',

    'FLOAT_PARAM_BTN',
    'FLOAT_PARAM_MENU',

    'STRING_PARAM_BTN',
    'STRING_PARAM_MENU',

    'PROPERTIES_BTN',
    'PROPERTIES_MENU',
]


from eventry.asyncio.callable_wrappers import CallableWrapper
from .default_builders import (
    build_parameter_button,
    properties_menu_builder,
    build_parameter_change_menu,
    build_toggle_parameter_button,
    build_open_menu_button,
    choice_parameter_menu_builder
)


TOGGLE_BTN = CallableWrapper(build_toggle_parameter_button)

INT_PARAM_BTN = STRING_PARAM_BTN = FLOAT_PARAM_BTN = CallableWrapper(build_parameter_button)
INT_PARAM_MENU = STRING_PARAM_MENU = FLOAT_PARAM_MENU = CallableWrapper(build_parameter_change_menu)

PROPERTIES_BTN = CallableWrapper(build_open_menu_button)
PROPERTIES_MENU = CallableWrapper(properties_menu_builder)

CHOICE_PARAM_BTN = CallableWrapper(build_open_menu_button)
CHOICE_PARAM_MENU = CallableWrapper(choice_parameter_menu_builder)