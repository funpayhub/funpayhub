from __future__ import annotations

from aiogram import BaseMiddleware


class AddDataMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        data['data'] = data
        print(data)
        await handler(event, data)
