from __future__ import annotations

from typing import Any

from funpaybotengine import Bot
from funpaybotengine.runner.runner import EventsStack
from funpaybotengine.dispatching.events import NewSaleEvent


async def make_profile_snapshot_middleware(
    event: NewSaleEvent,
    events_stack: EventsStack,
    bot: Bot,
) -> dict[str, Any] | None:
    if events_stack.get('profile_snapshot'):
        events_stack.get('profile_snapshot')

    for i in events_stack.events:
        if not isinstance(i, NewSaleEvent):
            continue
        events_stack['profile_snapshot'] = await bot.get_profile_page(bot.userid)
        events_stack.get('profile_snapshot')
    else:
        return None
