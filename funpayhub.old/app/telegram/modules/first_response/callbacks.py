from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class OpenAddGreetingsToOfferMenu(CallbackData, identifier='open_add_greetings_to_offer_menu'):
    pass


class BindGreetings(CallbackData, identifier='bind_greetings'):
    offer_id: str


class RemoveGreetings(CallbackData, identifier='remove_greetings'):
    offer_id: str
    execute_next: str = ''


class ClearGreetingsCache(CallbackData, identifier='clear_greetings_cache'): ...
