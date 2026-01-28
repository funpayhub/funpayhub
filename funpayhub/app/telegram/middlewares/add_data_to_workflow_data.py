from __future__ import annotations


__all__ = ['AddDataMiddleware']


from aiogram import BaseMiddleware


class AddDataMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data) -> None:
        data['data'] = data
        await handler(event, data)
