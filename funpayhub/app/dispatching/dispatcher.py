from __future__ import annotations


__all__ = ('Dispatcher',)


from typing import Any

from eventry.asyncio.dispatcher import Dispatcher as BaseDispatcher

from .router import Router
from .events.base import HubEvent, ErrorEvent


def error_event_factory(event: HubEvent, exception: Exception) -> ErrorEvent:
    return ErrorEvent(exception=exception, event=event)


class Dispatcher(BaseDispatcher, Router):
    def __init__(self, workflow_data: dict[str, Any] | None = None):
        BaseDispatcher.__init__(
            self,
            error_event_factory=error_event_factory,
            workflow_data=workflow_data,
        )

        Router.__init__(self, name='Dispatcher')
