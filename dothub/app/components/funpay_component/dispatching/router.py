from __future__ import annotations


__all__ = ['ComponentRouter']

from typing import Any
from collections.abc import Callable

from eventry.asyncio import (
    Router as EventryRouter,
    Context,
    FromContext,
    RouterConfig,
    MiddlewareStorage,
    DefaultHandlerManager,
)

from .events import (
    OffersRaisedEvent,
    ComponentStopEvent,
    ComponentStartEvent,
    ProfileUpdatedEvent,
)


class ComponentRouter(EventryRouter[Callable[..., Any]]):
    def __init__(self, name: str = '') -> None:
        super().__init__(
            name=name,
            config=RouterConfig(
                outer_mdw_args=(FromContext('next_call'), Context),
                inner_mdw_args=(FromContext('next_call'), Context),
            ),
        )

        self.middleware['router.outer'] = MiddlewareStorage()
        self.middleware['router.inner'] = MiddlewareStorage()

        self.on_component_start = self.add_handler_manager(
            DefaultHandlerManager(
                'on_component_start',
                ComponentStartEvent.__event_name__,
            ),
        )

        self.on_component_stop = self.add_handler_manager(
            DefaultHandlerManager(
                'on_component_stop',
                ComponentStopEvent.__event_name__,
            ),
        )

        self.on_profile_updated = self.add_handler_manager(
            DefaultHandlerManager(
                'on_profile_updated',
                ProfileUpdatedEvent.__event_name__,
            ),
        )

        self.on_offers_raised = self.add_handler_manager(
            DefaultHandlerManager(
                'on_offers_raised',
                OffersRaisedEvent.__event_name__,
            ),
        )

    @property
    def outer_middleware(self) -> MiddlewareStorage:
        return self.middleware['router.outer']

    @property
    def inner_middleware(self) -> MiddlewareStorage:
        return self.middleware['router.inner']
