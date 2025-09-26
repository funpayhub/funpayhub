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
    param.IntParameter: ui_builders.build_parameter_change_menu,
    param.FloatParameter: ui_builders.build_parameter_change_menu,
    param.StringParameter: ui_builders.build_parameter_change_menu,
    param.ChoiceParameter: ui_builders.choice_parameter_menu_builder,
    Properties: ui_builders.properties_menu_builder,
}


DEFAULT_MENUS: Final = {
    'fph-formatters-list': ui_builders.formatters_list_menu_builder,
    'fph-formatter-info': ui_builders.formatter_info_menu_builder,
}


DEFAULT_BUTTONS: Final = {
    'fph-formatters-list': ui_builders.build_formatters_button
}