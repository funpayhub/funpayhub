from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, ReactionTypeEmoji, ReactionTypePaid

from ... import callbacks as cbs, states
from funpayhub.app.telegram.ui.builders.context import SendMessageMenuContext
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.states import SendingFunpayMessage
from funpayhub.lib.telegram.ui import UIRegistry
from aiogram.types import Message
from funpaybotengine import Bot as FPBot
import asyncio

from .. import utils
from .router import router


@router.callback_query(cbs.SendMessage.filter())
async def set_sending_message_state(
    query: CallbackQuery,
    callback_data: cbs.SendMessage,
    tg_ui: UIRegistry,
    dispatcher: Dispatcher,
    bot: Bot,
):
    menu_context = SendMessageMenuContext(
        menu_id=MenuIds.send_funpay_message,
        funpay_chat_id=callback_data.to,
        trigger=query,
        menu_page=callback_data.menu_page,
        view_page=callback_data.view_page,
    )
    menu = await tg_ui.build_menu(menu_context, {})

    if callback_data.set_state:
        msg = await query.message.answer(
            text=menu.text,
            reply_markup=menu.total_keyboard(convert=True)
        )

        context = utils.get_context(dispatcher, bot, query)
        await context.clear()
        await context.set_state(states.SendingFunpayMessage.__identifier__)
        await context.set_data(
            {'data': states.SendingFunpayMessage(message=msg, to=callback_data.to)}
        )
        await query.answer()
    else:
        await menu.apply_to(query.message)


@router.message(StateFilter(states.SendingFunpayMessage.identifier))
async def send_funpay_message(
    message: Message,
    dispatcher: Dispatcher,
    bot: Bot,
    fp_bot: FPBot
):
    context = utils.get_context(dispatcher, bot, message)
    data: SendingFunpayMessage = (await context.get_data())['data']

    asyncio.create_task(utils.delete_message(data.message))

    await context.clear()

    result = False
    try:
        await fp_bot.send_message(
            chat_id=data.to,
            text=message.text,
        )
        result = True
    except:
        pass

    if result:
        await message.react(reaction=[ReactionTypeEmoji(emoji="👍")], is_big=True)
    else:
        reaction = ReactionTypePaid()
        await message.react(reaction=[ReactionTypeEmoji(emoji= "💩"), reaction], is_big=True)
    # todo: formatting