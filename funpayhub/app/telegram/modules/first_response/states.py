from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import StateFromQuery


if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class BindingFirstResponseToOffer(
    StateFromQuery, identifier='fph:binding_first_response_to_offer'
):
    state_message: Message
