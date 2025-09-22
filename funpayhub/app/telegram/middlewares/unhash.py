from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from funpayhub.lib.telegram.callbacks import Hash


if TYPE_CHECKING:
    from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000


class UnpackMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data):
        callback_data = event.data
        if event.data.startswith(f'{Hash.__prefix__}{Hash.__separator__}'):
            unpacked = Hash.unpack(event.data)
            hashinator: HashinatorT1000 = data['hashinator']
            callback_data = hashinator.unhash(unpacked.hash)
            if not callback_data:
                await event.answer(text='Ваще не знаю че это за кнопка', show_alert=True)
                return

        split = callback_data.split('->')
        data['callbacks_history'] = split[:-1]
        event.__dict__['data'] = split[-1]
        await handler(event, data)
