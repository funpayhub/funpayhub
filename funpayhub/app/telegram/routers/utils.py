from __future__ import annotations

from contextlib import suppress

from aiogram.types import Message


async def delete_message(msg: Message) -> None:
    with suppress(Exception):
        await msg.delete()
