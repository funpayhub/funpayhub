from __future__ import annotations


__all__ = [
    'TelegramStartEvent',
    'FunPayStartEvent',
    'OffersRaisedEvent',
]

from typing import Any

from funpaybotengine.types import Category

from .base import HubEvent


class TelegramStartEvent(HubEvent, name='fph:telegram_start'):
    def __init__(self) -> None:
        super().__init__()


class FunPayStartEvent(HubEvent, name='fph:funpay_start'):
    def __init__(self) -> None:
        super().__init__()


class OffersRaisedEvent(HubEvent, name='fph:offers_raised'):
    def __init__(self, category: Category) -> None:
        super().__init__()
        self._category = category

    @property
    def category(self) -> Category:
        return self._category

    @property
    def event_context_injection(self) -> dict[str, Any]:
        result = super().event_context_injection
        return result | {'category': self.category}
