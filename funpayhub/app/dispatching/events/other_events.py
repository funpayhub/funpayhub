from __future__ import annotations


__all__ = [
    'TelegramStartEvent',
]


from .base import HubEvent


class TelegramStartEvent(HubEvent):
    def __init__(self):
        super().__init__()
