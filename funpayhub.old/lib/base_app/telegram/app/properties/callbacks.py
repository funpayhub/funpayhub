from __future__ import annotations

from typing import Literal

from funpayhub.lib.telegram.callback_data import CallbackData


class NextParamValue(CallbackData, identifier='next_param_value'):
    path: list[str | int]


class ChooseParamValue(CallbackData, identifier='choose_param_value'):
    path: list[str | int]
    choice_id: str


class ManualParamValueInput(CallbackData, identifier='manual_value_input'):
    path: list[str | int]


# list param
class ListParamItemAction(CallbackData, identifier='list_item_action'):
    path: list[str | int]
    item_index: int
    action: Literal['remove', 'move_up', 'move_down', None] = None


class ListParamAddItem(CallbackData, identifier='list_param_add_item'):
    path: list[str | int]
