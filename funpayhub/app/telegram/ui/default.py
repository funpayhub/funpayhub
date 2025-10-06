from __future__ import annotations

from typing import Final

from funpayhub.lib.properties import Properties, parameter as param

from . import default_builders as ui_builders


DEFAULT_ENTRIES_BUTTONS: Final = {
    param.ToggleParameter: ui_builders.build_toggle_parameter_button,
    param.IntParameter: ui_builders.build_parameter_button,
    param.FloatParameter: ui_builders.build_parameter_button,
    param.StringParameter: ui_builders.build_parameter_button,
    param.ChoiceParameter: ui_builders.build_open_menu_button,
    Properties: ui_builders.build_open_menu_button,
}

DEFAULT_ENTRIES_MENUS: Final = {
    param.IntParameter: ui_builders.parameter_menu_builder,
    param.FloatParameter: ui_builders.parameter_menu_builder,
    param.StringParameter: ui_builders.parameter_menu_builder,
    param.ChoiceParameter: ui_builders.choice_parameter_menu_builder,
    Properties: ui_builders.properties_menu_builder,
}


DEFAULT_MENUS: Final = {
    'fph-formatters-list': ui_builders.formatters_list_menu_builder,
    'fph-formatter-info': ui_builders.formatter_info_menu_builder,
}


ENTRIES_BUTTONS_MODIFICATIONS: Final = {}


ENTRIES_MENUS_MODIFICATIONS: Final = {
    'fph:funpayhub_properties_menu_modification': ui_builders.funpayhub_properties_menu_modification,
    'fph:command_response_text_param_menu_modification': ui_builders.add_formatters_list_button_modification,
}


MENUS_MODIFICATIONS: Final = {}