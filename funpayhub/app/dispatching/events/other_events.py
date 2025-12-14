from __future__ import annotations


__all__ = [
    'TelegramStartEvent',
    'FunPayStartEvent',
]


from .base import HubEvent


class TelegramStartEvent(HubEvent):
    def __init__(self) -> None:
        super().__init__()


class FunPayStartEvent(HubEvent):
    def __init__(self) -> None:
        super().__init__()
