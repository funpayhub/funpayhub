from __future__ import annotations

from dataclasses import dataclass

from hubplatform.telegram.fsm import State


@dataclass
class AddingAutoResponseRule(State, identifier='app:funpay_componant:adding_auto_response_rule'):
    session_id: str
    from_session_id: str
