from .registry import PropertiesUIRegistry as Registry
from . import builders
from funpayhub.lib.properties import parameter as param, Properties


Registry.add_menu_builder(param.IntParameter, builders.parameter_menu_builder)
Registry.add_menu_builder(param.FloatParameter, builders.parameter_menu_builder)
Registry.add_menu_builder(param.StringParameter, builders.parameter_menu_builder)
Registry.add_menu_builder(param.ChoiceParameter, builders.choice_parameter_menu_builder)
Registry.add_menu_builder(param.ListParameter, builders.list_parameter_menu_builder)
Registry.add_menu_builder(Properties, builders.properties_menu_builder)

Registry.add_button_builder(param.ToggleParameter, builders.toggle_param_button_builder)
Registry.add_button_builder(param.IntParameter, builders.parameter_button_builder)
Registry.add_button_builder(param.FloatParameter, builders.parameter_button_builder)
Registry.add_button_builder(param.StringParameter, builders.parameter_button_builder)
Registry.add_button_builder(param.ChoiceParameter, builders.build_open_entry_menu_button)
Registry.add_button_builder(param.ListParameter, builders.build_open_entry_menu_button)
Registry.add_button_builder(Properties, builders.build_open_entry_menu_button)

entry_button_builder = Registry.entry_button_builder
entry_menu_builder = Registry.entry_menu_builder
