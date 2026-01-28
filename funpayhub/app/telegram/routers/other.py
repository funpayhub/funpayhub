from __future__ import annotations

from typing import TYPE_CHECKING
from contextlib import suppress

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.exceptions import AiogramError

import exit_codes
import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.translater import Translater


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
async def restart(message: Message, hub: FunPayHub, translater: Translater):
    await message.reply(translater.translate('$restarting'))
    await hub.shutdown(exit_codes.RESTART)


@router.message(Command('safe_mode'))
async def safe_mode(message: Message, hub: FunPayHub, translater: Translater):
    if hub.safe_mode:
        await message.reply(translater.translate('$already_in_safe_mode'))
        return

    await message.reply(translater.translate('$restarting_in_safe_mode'))
    await hub.shutdown(exit_codes.RESTART_SAFE)


@router.message(Command('standard_mode'))
async def standard_mode(message: Message, hub: FunPayHub, translater: Translater):
    if not hub.safe_mode:
        await message.reply(translater.translate('$already_in_standard_mode'))
        return

    await message.reply(translater.translate('$restarting_in_standard_mode'))
    await hub.shutdown(exit_codes.RESTART_NON_SAFE)


@r.callback_query(cbs.ShutDown.filter())
async def shutdown(
    query: CallbackQuery, hub: FunPayHub, callback_data: cbs.ShutDown, translater: Translater
) -> None:
    texts = {
        exit_codes.SHUTDOWN: '$shutting_down',
        exit_codes.RESTART: '$restarting',
        exit_codes.RESTART_SAFE: '$restarting_in_safe_mode',
        exit_codes.RESTART_NON_SAFE: '$restarting_in_standard_mode',
    }
    text = texts.get(callback_data.exit_code, '$shutting_down')

    try:
        await query.answer(text=translater.translate(text), show_alert=True)
    except:
        pass

    await hub.shutdown(callback_data.exit_code)


@r.startup()
async def startup(hub: FunPayHub):
    with suppress(AiogramError):
        await hub.telegram.bot.set_my_description("""🤖 FunPayHub — лучший инструмент для автоматизации продаж на FunPay!
    🚀 Автовыдача товаров
    📈 Автоподнятие лотов
    💬 Автоответ на сообщения
    ⚙️ Команды, хуки, форматтеры, чего тут только нет (мне было лень вспоминать)
    🧩 Модульная система, поддержка плагинов
    🔧 Множество настроек и кастомизация
    
    …и многое другое, чтобы полностью контролировать продажи и экономить время!
    
    💻 Github: https://github.com/funpayhub/funpayhub
    💬 Чат проекта: https://t.me/funpay_hub""")

        await hub.telegram.bot.set_my_short_description(
            '🤖 Лучший бот для автоматизации продаж на FunPay!\n'
            '💬 Чат проекта: https://t.me/funpay_hub',
        )
