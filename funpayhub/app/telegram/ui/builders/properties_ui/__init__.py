from __future__ import annotations

from funpayhub.lib.properties import Properties, parameter as param
from funpayhub.app.telegram.ui.ids import MenuIds, ButtonIds

from .registry import EntriesUIRegistry as Registry


Registry.add_menu_builder(param.IntParameter, MenuIds.param_value_manual_input)
Registry.add_menu_builder(param.FloatParameter, MenuIds.param_value_manual_input)
Registry.add_menu_builder(param.StringParameter, MenuIds.param_value_manual_input)
Registry.add_menu_builder(param.ChoiceParameter, MenuIds.properties_choice_param)
Registry.add_menu_builder(param.ListParameter, MenuIds.properties_list_param)
Registry.add_menu_builder(Properties, MenuIds.properties_properties)

Registry.add_button_builder(param.ToggleParameter, ButtonIds.properties_toggle_param)
Registry.add_button_builder(param.IntParameter, ButtonIds.properties_change_param_value)
Registry.add_button_builder(param.FloatParameter, ButtonIds.properties_change_param_value)
Registry.add_button_builder(param.StringParameter, ButtonIds.properties_change_param_value)
Registry.add_button_builder(param.ChoiceParameter, ButtonIds.properties_open_param_menu)
Registry.add_button_builder(param.ListParameter, ButtonIds.properties_open_param_menu)
Registry.add_button_builder(Properties, ButtonIds.properties_open_param_menu)
