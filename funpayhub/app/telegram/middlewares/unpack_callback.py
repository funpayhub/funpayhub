from __future__ import annotations


__all__ = ['UnpackMiddleware']


from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from funpayhub.lib.telegram.callback_data import CallbackData
from funpayhub.lib.telegram.callback_data.hashinator import BadHashError, HashinatorT1000


class UnpackMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data) -> None:
        callback_data = event.data
        if HashinatorT1000.is_hash(event.data):
            try:
                HashinatorT1000.unhash(event.data)
            except BadHashError:
                await event.answer(text='Ваще не знаю че это за кнопка', show_alert=True)
                return
        parsed = CallbackData.parse(callback_data)

        data['unpacked_callback'] = parsed
        event.__dict__.update({'__parsed__': parsed, 'data': callback_data})
        print(f'Unpacked callback data: {event.data}')
        print(f'Callback: {parsed.identifier}')
        print(f'Callback data: {parsed.data}')
        print('Callback history:')
        for i in parsed.history:
            print(f'    {i}')
        await handler(event, data)
