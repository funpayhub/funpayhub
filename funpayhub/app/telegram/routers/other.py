from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from funpayhub.lib.translater import Translater

import exit_codes
import funpayhub.app.telegram.callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


router = r = Router(name='fph:other')


# Commands
@router.message(Command('shutdown'))
async def shutdown(message: Message, hub: FunPayHub):
    await message.answer_animation(
        'CAACAgIAAxkBAAIBgml58y4453QL1LPOC20gPjjdTi9cAALNiwACP73RS_9mGlmKls_5OAQ',
    )
    await hub.shutdown(exit_codes.SHUTDOWN)


@router.message(Command('restart'))
async def restart(message: Message, hub: FunPayHub):
    await message.reply('$shutting_down')
    await hub.shutdown(exit_codes.RESTART)


@router.message(Command('safe_mode'))
async def safe_mode(message: Message, hub: FunPayHub):
    if hub.safe_mode:
        await message.reply('$already_in_safe_mode')
        return

    await message.reply('$shutting_down')
    await hub.shutdown(exit_codes.RESTART_SAFE)


@router.message(Command('standard_mode'))
async def standard_mode(message: Message, hub: FunPayHub):
    if not hub.safe_mode:
        await message.reply('$already_in_standard_mode')
        return

    await message.reply('$shutting_down')
    await hub.shutdown(exit_codes.RESTART_NON_SAFE)


@r.callback_query(cbs.ShutDown.filter())
async def shutdown(query: CallbackQuery, hub: FunPayHub, callback_data: cbs.ShutDown) -> None:
    try:
        await query.answer(text='$shutting_down', show_alert=True)
    except:
        pass

    await hub.shutdown(callback_data.exit_code)
