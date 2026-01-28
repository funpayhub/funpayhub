from __future__ import annotations


__all__ = [
    'StatesManager',
    'STATES_MANAGER_KEY',
]

from typing import TYPE_CHECKING
from collections import defaultdict


if TYPE_CHECKING:
    from .state import State


STATES_MANAGER_KEY = 'states_manager'


class StatesManager:
    def __init__(self) -> None:
        self.states = defaultdict(dict)

    def set_state(
        self,
        user_id: int,
        chat_id: int,
        state: State,
        thread_id: int | None = None,
    ) -> None:
        self.states[user_id][f'{chat_id}.{thread_id}'] = state

    def get_state(self, user_id: int, chat_id: int, thread_id: int | None = None) -> State | None:
        if user_id not in self.states:
            return None

        if f'{chat_id}.{thread_id}' not in self.states[user_id]:
            return None

        return self.states[user_id][f'{chat_id}.{thread_id}']

    def clear_state(self, user_id: int, chat_id: int, thread_id: int | None = None) -> None:
        if user_id not in self.states:
            return

        if f'{chat_id}.{thread_id}' not in self.states[user_id]:
            return

        del self.states[user_id][f'{chat_id}.{thread_id}']
        if not self.states[user_id]:
            del self.states[user_id]
