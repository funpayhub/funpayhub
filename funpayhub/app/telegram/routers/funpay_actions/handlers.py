from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery

from funpayhub.lib.telegram import callbacks as cbs
from funpayhub.lib.telegram import states
from funpayhub.app.telegram.ui.builders.context import SendMessageMenuContext
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui import UIRegistry

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
