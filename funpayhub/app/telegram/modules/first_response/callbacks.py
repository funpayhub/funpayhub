from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class OpenAddFirstResponseToOfferMenu(
    CallbackData,
    identifier='open_add_first_response_to_offer_menu',
):
    pass


class BindFirstResponseToOffer(CallbackData, identifier='bind_first_response_to_offer_menu'):
    offer_id: str


class RemoveFirstResponseToOffer(CallbackData, identifier='remove_first_response_to_offer_menu'):
    offer_id: str
    execute_next: str = ''


class ClearFirstResponseCache(CallbackData, identifier='clear_first_response_cache'):
    execute_next: str = ''
