from __future__ import annotations

import asyncio
from contextlib import suppress

from aiogram.types import Message


async def _delete_message(msg: Message) -> None:
    with suppress(Exception):
        await msg.delete()


def delete_message(msg: Message) -> None:
    asyncio.create_task(_delete_message(msg))
