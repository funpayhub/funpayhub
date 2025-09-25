from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from funpayhub.lib.telegram.callbacks import Hash
from funpayhub.lib.telegram.callback_data import CallbackData


if TYPE_CHECKING:
    from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000


class UnpackMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data):
        callback_data = event.data
        if event.data.endswith(f'}}{Hash.__identifier__}'):
            parsed = Hash.unpack(event.data)
            hashinator: HashinatorT1000 = data['hashinator']
            callback_data = hashinator.unhash(parsed.hash)
            if not callback_data:
                await event.answer(text='Ваще не знаю че это за кнопка', show_alert=True)
                return
            print(f'Unhashed: {parsed.hash} -> {callback_data}')
        parsed = CallbackData.parse(callback_data)

        print(f'Parsed: {callback_data}')
        print(f'Identifier: {parsed.identifier}')
        print(f'Data: {parsed.data}')
        print(f'History: {parsed.history}')

        data['unpacked_callback'] = parsed
        event.__dict__.update({'__parsed__': parsed, 'data': callback_data})
        await handler(event, data)
