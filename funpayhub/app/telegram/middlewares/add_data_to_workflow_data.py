from __future__ import annotations


__all__ = ['AddDataMiddleware']


from aiogram import BaseMiddleware


class AddDataMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        data['data'] = data
        await handler(event, data)
