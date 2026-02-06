from __future__ import annotations


__all__ = [
    'AddCommand',
    'RemoveCommand',
]


from funpayhub.lib.telegram.callback_data import CallbackData


class AddCommand(CallbackData, identifier='add_command'):
    pass


class RemoveCommand(CallbackData, identifier='remove_command'):
    command: str
