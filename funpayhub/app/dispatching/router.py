from __future__ import annotations


__all__ = ['Router']


from eventry.asyncio.router import Router as BaseRouter

from .handler_manager import HandlerManager


_events = {
    'parameter_value_changed',
    'node_attached',
    'telegram_start',
    'funpay_start',
    'offers_raised',
    'funpayhub_stopped',
}


class Router(BaseRouter):
    on_parameter_value_changed: HandlerManager
    on_node_attached: HandlerManager
    on_offers_raised: HandlerManager
    on_telegram_start: HandlerManager
    on_funpay_start: HandlerManager
    on_funpayhub_stopped: HandlerManager

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name or f'Router{id(self)}')
        self.set_default_handler_manager(HandlerManager(self, 'default', None))

        for name in _events:
            manager = self._add_handler_manager(HandlerManager(self, f'on_{name}', f'fph:{name}'))
            setattr(self, f'on_{name}', manager)

    @property
    def on_event(self) -> HandlerManager:
        return self._default_handler_manager
