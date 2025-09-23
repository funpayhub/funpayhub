from __future__ import annotations

import json
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
            print(f'Unhashed: {unpacked.hash} -> {callback_data}')

        split = callback_data.split('->')
        data['callbacks_history'] = split[:-1]

        current_callback = split[-1]
        split = current_callback.split('~')
        if len(split) < 2:
            event.__dict__['data'] = current_callback
            data['callback_args'] = {}
        else:
            event.__dict__['data'] = split[1]
            data['callback_args'] = json.loads(split[0])
        data['current_callback'] = current_callback

        print(f'Callback: {current_callback}\nHistory: {data["callbacks_history"]}\nArgs: {data["callback_args"]}')

        await handler(event, data)
