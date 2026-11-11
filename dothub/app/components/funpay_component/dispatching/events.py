from __future__ import annotations


__all__ = [
    'FunPayComponentEvent',
    'ComponentStartEvent',
    'ComponentStopEvent',
    'ProfileUpdatedEvent',
    'OffersRaisedEvent',
]

from typing import Any
from collections.abc import Sequence

from eventry.asyncio import ExtendedEvent
from funpaybotengine.types import Category
from funpaybotengine.types.pages import ProfilePage


class FunPayComponentEvent(ExtendedEvent, event_name='__funpay_component_event__'):
    pass


class ComponentStartEvent(FunPayComponentEvent, event_name='funpay_component_start'):
    pass


class ComponentStopEvent(FunPayComponentEvent, event_name='funpay_component_stop'):
    pass


class ProfileUpdatedEvent(FunPayComponentEvent, event_name='funpay_component_profile_updated'):
    def __init__(self, profile: ProfilePage) -> None:
        super().__init__()
        self._profile = profile

    @property
    def profile(self) -> ProfilePage:
        return self._profile

    def context_injection(self) -> dict[str, Any]:
        return super().context_injection() | {'profile': self._profile}


class OffersRaisedEvent(FunPayComponentEvent, event_name='funpay_component_offers_raised'):
    def __init__(
        self,
        category: Category,
        subcategory_ids: Sequence[int],
        next_raise_at: float | None,
    ) -> None:
        super().__init__()
        self._category = category
        self._subcategory_ids = tuple(subcategory_ids)
        self._next_raise_at = next_raise_at

    @property
    def category(self) -> Category:
        return self._category

    @property
    def subcategory_ids(self) -> tuple[int, ...]:
        return self._subcategory_ids

    @property
    def next_raise_at(self) -> float | None:
        """Unix time of the next raise attempt of this category."""
        return self._next_raise_at

    def context_injection(self) -> dict[str, Any]:
        return super().context_injection() | {
            'category': self._category,
            'subcategory_ids': self._subcategory_ids,
            'next_raise_at': self._next_raise_at,
        }
