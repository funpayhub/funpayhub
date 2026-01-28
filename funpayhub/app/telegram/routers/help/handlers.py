from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router, BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

import funpayhub.app.telegram.callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.lib.translater import Translater


router = Router(name='fph:help')


need_help = set()


class NeedHelpMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data) -> None:
        if event.from_user.id not in need_help:
            await handler(event, data)
            return

        await router.propagate_event('callback_query', event, **data)


@router.message(Command('help'))
async def help_command(message: Message) -> None:
    if message.from_user.id in need_help:
        need_help.remove(message.from_user.id)
        await message.answer('Вы вышли из режима справки.')
    else:
        need_help.add(message.from_user.id)
        await message.answer('Вы вошли в режим справки. Снова введите /help для выхода.')


@router.callback_query(cbs.OpenEntryMenu.filter())
@router.callback_query(cbs.NextParamValue.filter())
@router.callback_query(cbs.ManualParamValueInput.filter())
async def show_entry_help(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.OpenEntryMenu,
    translater: Translater,
):
    entry = properties.get_entry(callback_data.path)
    desc = translater.translate(entry.description)

    await query.answer(
        text=f'Справка:\n{desc}',
        show_alert=True,
    )
