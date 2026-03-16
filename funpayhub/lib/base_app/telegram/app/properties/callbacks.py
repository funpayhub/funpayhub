from __future__ import annotations

from typing import Literal

from funpayhub.lib.telegram.callback_data import UICallbackData


class NextParamValue(UICallbackData, identifier='next_param_value'):
    path: list[str | int]


class ChooseParamValue(UICallbackData, identifier='choose_param_value'):
    path: list[str | int]
    choice_id: str


class ManualParamValueInput(UICallbackData, identifier='manual_value_input'):
    path: list[str | int]


# list param
class ListParamItemAction(UICallbackData, identifier='list_item_action'):
    path: list[str | int]
    item_index: int
    action: Literal['remove', 'move_up', 'move_down', None] = None


class ListParamAddItem(UICallbackData, identifier='list_param_add_item'):
    path: list[str | int]
