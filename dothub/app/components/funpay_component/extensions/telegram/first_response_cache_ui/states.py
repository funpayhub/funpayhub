from __future__ import annotations

from typing import Literal
from dataclasses import dataclass

from hubplatform.telegram.fsm import State


@dataclass
class EnteringChatData(
    State,
    identifier='app:funpay_component:telegram_extension:first_response_cache:entering_chat_data',
):
    action: Literal['add', 'set_time']
    return_session_id: str
    input_session_id: str
    chat_id: int | None = None
