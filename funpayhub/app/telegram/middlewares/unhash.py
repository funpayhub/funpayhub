from __future__ import annotations
from typing import TYPE_CHECKING
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from funpayhub.lib.telegram.callbacks import Hash

if TYPE_CHECKING:
    from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000


class UnhashMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data):
        if not event.data.startswith('hash:'):
            await handler(event, data)
            return

        unpacked = Hash.unpack(event.data)
        hashinater: HashinatorT1000 = data['keyboard_hashinater']
        real_data = hashinater.unhash(unpacked.hash)

        if real_data is None:
            await event.answer(text='Ваще не знаю че это за кнопка', show_alert=True)
            return

        new_event = event.model_copy(update={'data': real_data}, deep=False)
        await handler(new_event, data)