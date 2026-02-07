from __future__ import annotations

from typing import TYPE_CHECKING
from io import BytesIO

from aiogram.types import Message, CallbackQuery, ReactionTypeEmoji
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.app.telegram.states import SendingFunpayMessage
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.base_app.telegram import utils
from funpayhub.app.telegram.ui.builders.context import SendMessageMenuContext
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from ... import states, callbacks as cbs
from .router import router


if TYPE_CHECKING:
    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram


@router.callback_query(cbs.SendMessage.filter())
async def set_sending_message_state(
    query: CallbackQuery,
    callback_data: cbs.SendMessage,
    tg_ui: UIRegistry,
    state: FSMContext,
) -> None:
    menu_context = SendMessageMenuContext(
        menu_id=MenuIds.send_funpay_message,
        trigger=query,
        funpay_chat_id=callback_data.to,
        funpay_chat_name=callback_data.name,
        callback_override=callback_data.copy_history(
            OpenMenu(
                menu_id=MenuIds.send_funpay_message,
                context_data={
                    'funpay_chat_id': callback_data.to,
                    'funpay_chat_name': callback_data.name,
                },
            ),
        ),
    )

    menu = await tg_ui.build_menu(menu_context)

    msg = await query.message.answer(
        text=menu.main_text,
        reply_markup=menu.total_keyboard(convert=True),
    )

    await state.set_state(states.SendingFunpayMessage.__identifier__)
    await state.set_data(
        {'data': states.SendingFunpayMessage(message=msg, to=callback_data.to)},
    )
    await query.answer()


@router.message(StateFilter(states.SendingFunpayMessage.identifier))
async def send_funpay_message(
    message: Message,
    fp: FunPay,
    tg: Telegram,
    state: FSMContext,
) -> None:
    data: SendingFunpayMessage = (await state.get_data())['data']
    utils.delete_message(data.message)
    await state.clear()

    image = None
    text = message.text
    if message.photo:
        file = await tg.bot.get_file(message.photo[-1].file_id)
        buffer = BytesIO()
        await tg.bot.download_file(file.file_path, destination=buffer)
        image = buffer
        text = None

    result = False
    try:
        await fp.send_message(
            chat_id=data.to,
            text=text,
            image=image,
            automatic_message=False,
        )
        result = True
    except Exception:
        import traceback

        print(traceback.format_exc())  # todo: logging

    if result:
        await message.react(reaction=[ReactionTypeEmoji(emoji='👍')])
    else:
        await message.react(reaction=[ReactionTypeEmoji(emoji='💩')])
    # todo: execute $formatters
