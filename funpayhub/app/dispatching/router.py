from __future__ import annotations


__all__ = ['Router']


from eventry.asyncio.router import Router as BaseRouter

from . import events
from .handler_manager import HandlerManager


_events = {
    'parameter_value_changed': events.ParameterValueChangedEvent,
    'properties_attached': events.PropertiesAttachedEvent,
    'parameter_attached': events.ParameterAttachedEvent,
    'telegram_start': events.TelegramStartEvent,
    'funpay_start': events.FunPayStartEvent,
    'offers_raised': events.OffersRaisedEvent,
}


class Router(BaseRouter):
    on_parameter_value_changed: HandlerManager
    on_properties_attached: HandlerManager
    on_parameter_attached: HandlerManager
    on_offers_raised: HandlerManager
    on_telegram_start: HandlerManager
    on_funpay_start: HandlerManager

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name or f'Router{id(self)}')
        self.set_default_handler_manager(HandlerManager(self, 'default', None))

        for name, event in _events.items():
            manager = self._add_handler_manager(HandlerManager(self, name, event))  # type: ignore
            setattr(self, f'on_{name}', manager)

    @property
    def on_event(self) -> HandlerManager:
        return self._default_handler_manager
