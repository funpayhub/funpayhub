from __future__ import annotations

from typing import TYPE_CHECKING, Any
from io import BytesIO

from aiogram.types import Message, ReactionTypeEmoji

from funpayhub.lib.base_app.telegram import utils

from funpayhub.app.telegram.states import SendingFunpayMessage
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import SendMessageMenuContext

from ... import (
    states,
    callbacks as cbs,
)
from .router import router


if TYPE_CHECKING:
    from aiogram.types import CallbackQuery as Query
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram


@router.callback_query(cbs.SendMessage.filter())
async def sending_message_state(q: Query, cbd: cbs.SendMessage, state: FSM) -> None:
    msg = await SendMessageMenuContext(
        menu_id=MenuIds.send_funpay_message,
        trigger=q,
        funpay_chat_id=cbd.to,
        funpay_chat_name=cbd.name,
    ).answer_to()
    await states.SendingFunpayMessage(query=q, state_msg=msg, to=cbd.to).set(state)


@router.message(states.SendingFunpayMessage.filter())
async def send_funpay_message(m: Message, fp: FunPay, tg: Telegram, state: FSM) -> Any:
    data = await SendingFunpayMessage.clear(state, raise_=True)
    utils.delete_message(data.state_msg)

    image, text = None, m.text
    if m.photo:
        file = await tg.bot.get_file(m.photo[-1].file_id)
        buffer = BytesIO()
        await tg.bot.download_file(file.file_path, destination=buffer)
        image = buffer
        text = None

    try:
        await fp.send_message(chat_id=data.to, text=text, image=image, automatic_message=False)
    except Exception:
        import traceback

        print(traceback.format_exc())  # todo: logging
        return m.react(reaction=[ReactionTypeEmoji(emoji='💩')])

    return m.react(reaction=[ReactionTypeEmoji(emoji='👍')])
    # todo: execute $formatters
