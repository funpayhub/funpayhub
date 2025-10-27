from __future__ import annotations

from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


async def delete_message(msg: Message):
    with suppress(Exception):
        await msg.delete()


def get_context(dp: Dispatcher, bot: Bot, obj: Message | CallbackQuery) -> FSMContext:
    msg = obj if isinstance(obj, Message) else obj.message
    return dp.fsm.get_context(
        bot=bot,
        chat_id=msg.chat.id,
        thread_id=msg.message_thread_id,
        user_id=obj.from_user.id,
    )
