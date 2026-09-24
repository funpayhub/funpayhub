from __future__ import annotations

from dataclasses import dataclass

from hubplatform.telegram.fsm import State


@dataclass
class AddingAutoDeliveryRule(State, identifier='fph:adding_autodelivery_rule'):
    open_session: str
    delete_message: int | None = None


@dataclass
class BindingGoodsSource(State, identifier='fph:binding_goods_source'):
    open_session: str
    rule: str
    delete_session: str | None = None
