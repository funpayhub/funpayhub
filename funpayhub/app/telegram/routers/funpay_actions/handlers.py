from aiogram import Dispatcher, Bot
from aiogram.types import CallbackQuery

from .router import router
from funpayhub.lib.telegram import callbacks as cbs
from .. import utils


@router.callback_query(cbs.SendMessage.filter())
async def set_sending_message_state(
    query: CallbackQuery,
    callback_data: cbs.SendMessage,
    dispatcher: Dispatcher,
    bot: Bot,
):
    context = utils.get_context(dispatcher, bot, query)
    await context.clear()


