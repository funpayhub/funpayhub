from __future__ import annotations


__all__ = ('HandlerManager',)

from typing import TYPE_CHECKING, Any, Type

from eventry.asyncio.default_types import FilterType, HandlerType, MiddlewareType
from eventry.asyncio.handler_manager import HandlerManager as BaseHandlerManager
from eventry.asyncio.middleware_manager import MiddlewareManager, MiddlewareManagerTypes

from .events.base import HubEvent


if TYPE_CHECKING:
    from .router import Router


class HandlerManager(BaseHandlerManager[FilterType, HandlerType, MiddlewareType, 'Router']):
    def __init__(
        self,
        router: 'Router',
        handler_manager_id: str,
        event_type_filter: Type[HubEvent] | None,
    ):
        super().__init__(
            router=router,
            handler_manager_id=handler_manager_id,
            event_type_filter=event_type_filter,
        )

        self._add_middleware_manager(MiddlewareManagerTypes.GLOBAL, MiddlewareManager())
        self._add_middleware_manager(MiddlewareManagerTypes.OUTER_PER_HANDLER, MiddlewareManager())
        self._add_middleware_manager(MiddlewareManagerTypes.INNER_PER_HANDLER, MiddlewareManager())

    @property
    def inner_middleware(self) -> MiddlewareManager:
        return self.middleware_manager(MiddlewareManagerTypes.INNER_PER_HANDLER)  # type: ignore  # not None

    @property
    def outer_middleware(self) -> MiddlewareManager:
        return self.middleware_manager(MiddlewareManagerTypes.OUTER_PER_HANDLER)  # type: ignore  # not None

    @property
    def global_middleware(self) -> MiddlewareManager:
        return self.middleware_manager(MiddlewareManagerTypes.GLOBAL)  # type: ignore  # not None
