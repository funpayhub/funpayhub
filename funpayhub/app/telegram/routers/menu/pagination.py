from aiogram import Router, Bot, Dispatcher
from aiogram.types import CallbackQuery, Update
import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.callbacks_parsing import UnpackedCallback, join_callbacks, unpack_callback
import re


router = Router(name='fph:pagination')


@router.callback_query(cbs.ChangePageTo.filter())
async def change_page(
    query: CallbackQuery,
    unpacked_callback: UnpackedCallback,
    dispatcher: Dispatcher,
    bot: Bot,
):
    unpacked = cbs.ChangePageTo.unpack(query.data)
    old = unpack_callback(unpacked_callback.history[-1])
    old.current_callback = re.sub(
        r'page-\d+',
        f'page-{unpacked.page}',
        old.current_callback
    )
    unpacked_callback.history[-1] = old.pack()
    # todo: better parsing

    new_event = query.model_copy(update={'data': join_callbacks(*unpacked_callback.history)})
    update = Update(
        update_id=0,
        callback_query=new_event,
    )
    await dispatcher.feed_update(bot, update)
