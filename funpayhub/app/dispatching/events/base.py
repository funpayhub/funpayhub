from __future__ import annotations

from typing import Any

from eventry.asyncio.event import ExtendedEvent


class HubEvent(ExtendedEvent, name='__hub_event__'): ...


class ErrorEvent(HubEvent, name='fph:error'):
    def __init__(self, exception: Exception, event: HubEvent) -> None:
        self.exception = exception
        self.event = event
        super().__init__()

    @property
    def event_context_injection(self) -> dict[str, Any]:
        return {
            'exception': self.exception,
            'in_event': self.event,
        }
