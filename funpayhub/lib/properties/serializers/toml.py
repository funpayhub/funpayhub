from funpayhub.lib.properties import MutableParameter, Properties
from typing import Any
import tomli_w


def serialize_parameter(param: MutableParameter[Any]) -> str:
    name = '\n'.join(f'# {i}' for i in param.name.split('\n'))
    desc = '\n'.join(f'# {i}' for i in param.description.split('\n'))
    val = tomli_w.dumps({param.id: param.serialized_value}, multiline_strings=True)
    return f'{name}\n{desc}\n{val}'


def serialize_properties(properties: Properties, same_file_only: bool = True) -> str:
    curr_str = ''
    for node in properties._nodes.values():
        if not isinstance(node, MutableParameter):
            continue
        curr_str += serialize_parameter(node) + '\n\n'

    for node in properties._nodes.values():
        if not isinstance(node, Properties):
            continue

        if same_file_only and node.file_to_save != properties.file_to_save:
            continue

