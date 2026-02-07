from __future__ import annotations


__all__ = [
    'NodesUIRegistry',
    'NodeMenuBuilder',
    'NodeButtonBuilder',
    'NodeMenuContext',
    'NodeButtonContext',
    'NodeMenuIds',
    'NodeButtonIds',
]

from funpayhub.lib.properties import (
    Properties,
    parameter as p,
)

from . import builders
from .context import NodeMenuContext, NodeButtonContext
from .registry import NodeMenuBuilder, NodesUIRegistry, NodeButtonBuilder


NodesUIRegistry.add_menu_builder(p.IntParameter, builders.ParamManualInputMenuBuilder.menu_id)
NodesUIRegistry.add_menu_builder(p.FloatParameter, builders.ParamManualInputMenuBuilder.menu_id)
NodesUIRegistry.add_menu_builder(p.StringParameter, builders.ParamManualInputMenuBuilder.menu_id)
NodesUIRegistry.add_menu_builder(p.ChoiceParameter, builders.ChoiceParameterMenuBuilder.menu_id)
NodesUIRegistry.add_menu_builder(p.ListParameter, builders.ListParameterMenuBuilder.menu_id)
NodesUIRegistry.add_menu_builder(Properties, builders.PropertiesMenuBuilder.menu_id)

NodesUIRegistry.add_button_builder(p.ToggleParameter, builders.ToggleParamButtonBuilder.button_id)
NodesUIRegistry.add_button_builder(
    p.IntParameter,
    builders.ChangeParamValueButtonBuilder.button_id,
)
NodesUIRegistry.add_button_builder(
    p.FloatParameter,
    builders.ChangeParamValueButtonBuilder.button_id,
)
NodesUIRegistry.add_button_builder(
    p.StringParameter,
    builders.ChangeParamValueButtonBuilder.button_id,
)
NodesUIRegistry.add_button_builder(
    p.ChoiceParameter,
    builders.OpenParamMenuButtonBuilder.button_id,
)
NodesUIRegistry.add_button_builder(p.ListParameter, builders.OpenParamMenuButtonBuilder.button_id)
NodesUIRegistry.add_button_builder(Properties, builders.OpenParamMenuButtonBuilder.button_id)


class NodeMenuIds:
    props_node = NodeMenuBuilder.menu_id
    props_param_manual_input = builders.ParamManualInputMenuBuilder.menu_id
    props_choice_param = builders.ChoiceParameterMenuBuilder.menu_id
    props_list_param = builders.ListParameterMenuBuilder.menu_id
    props_props = builders.PropertiesMenuBuilder.menu_id
    props_add_list_item = builders.AddListItemMenuBuilder.menu_id


class NodeButtonIds:
    props_node = NodeButtonBuilder.button_id
    props_toggle_param = builders.ToggleParamButtonBuilder.button_id
    props_change_param_value = builders.ChangeParamValueButtonBuilder.button_id
    props_open_param = builders.OpenParamMenuButtonBuilder.button_id
