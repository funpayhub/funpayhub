from __future__ import annotations

from typing import TYPE_CHECKING, Any
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import StateFromQuery


if TYPE_CHECKING:
    from aiogram.types import Message

    from funpayhub.lib.properties import ListParameter, MutableParameter


@dataclass
class ChangingParameterValue(StateFromQuery, identifier='fph:changing_parameter_value'):
    parameter: MutableParameter[Any]
    state_message: Message


@dataclass
class AddingListItem(StateFromQuery, identifier='fph:adding_list_item'):
    parameter: ListParameter[Any]
    state_message: Message
