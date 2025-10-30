from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery

from funpayhub.lib.telegram import callbacks as cbs

from .. import utils
from .router import router


@router.callback_query(cbs.SendMessage.filter())
async def set_sending_message_state(
    query: CallbackQuery,
    callback_data: cbs.SendMessage,
    dispatcher: Dispatcher,
    bot: Bot,
):
    context = utils.get_context(dispatcher, bot, query)
    await context.clear()
