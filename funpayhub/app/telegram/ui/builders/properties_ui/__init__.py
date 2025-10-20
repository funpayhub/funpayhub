from __future__ import annotations

from funpayhub.lib.properties import Properties, parameter as param

from . import builders
from .registry import EntriesUIRegistry as Registry


Registry.add_menu_builder(param.IntParameter, builders.param_value_manual_input_menu_builder)
Registry.add_menu_builder(param.FloatParameter, builders.param_value_manual_input_menu_builder)
Registry.add_menu_builder(param.StringParameter, builders.param_value_manual_input_menu_builder)
Registry.add_menu_builder(param.ChoiceParameter, builders.choice_parameter_menu_builder)
Registry.add_menu_builder(param.ListParameter, builders.list_parameter_menu_builder)
Registry.add_menu_builder(Properties, builders.properties_menu_builder)

Registry.add_button_builder(param.ToggleParameter, builders.toggle_param_button_builder)
Registry.add_button_builder(param.IntParameter, builders.parameter_button_builder)
Registry.add_button_builder(param.FloatParameter, builders.parameter_button_builder)
Registry.add_button_builder(param.StringParameter, builders.parameter_button_builder)
Registry.add_button_builder(param.ChoiceParameter, builders.open_entry_menu_button_builder)
Registry.add_button_builder(param.ListParameter, builders.open_entry_menu_button_builder)
Registry.add_button_builder(Properties, builders.open_entry_menu_button_builder)
