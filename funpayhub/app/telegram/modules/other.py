from __future__ import annotations

from typing import TYPE_CHECKING
from contextlib import suppress

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.exceptions import AiogramError

import exit_codes

from funpayhub.lib.translater import Translater


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


router = r = Router(name='fph:other')


# Commands
@router.message(Command('shutdown'))
async def shutdown(message: Message, hub: FunPayHub) -> None:
    await message.answer_animation(
        'CAACAgIAAxkBAAIBgml58y4453QL1LPOC20gPjjdTi9cAALNiwACP73RS_9mGlmKls_5OAQ',
    )
    await hub.shutdown(exit_codes.SHUTDOWN)


@router.message(Command('restart'))
async def restart(message: Message, hub: FunPayHub, translater: Translater) -> None:
    await message.reply(translater.translate('♻️ Перезапускаюсь...'))
    await hub.shutdown(exit_codes.RESTART)


@router.message(Command('safe_mode'))
async def safe_mode(message: Message, hub: FunPayHub, translater: Translater) -> None:
    if hub.safe_mode:
        await message.reply(translater.translate('⚠️ Уже в безопасном режиме.'))
        return

    await message.reply(translater.translate('♻️ Перезапускаюсь в безопасный режим...'))
    await hub.shutdown(exit_codes.RESTART_SAFE)


@router.message(Command('standard_mode'))
async def standard_mode(message: Message, hub: FunPayHub, translater: Translater) -> None:
    if not hub.safe_mode:
        await message.reply(translater.translate('⚠️ Уже в стандартном режиме.'))
        return

    await message.reply(translater.translate('♻️ Перезапускаюсь в стандартный режим...'))
    await hub.shutdown(exit_codes.RESTART_NON_SAFE)


@r.startup()
async def startup(hub: FunPayHub) -> None:
    with suppress(AiogramError):
        await hub.telegram.bot.set_my_description(
            '🤖 FunPay Hub — лучший инструмент для автоматизации продаж на FunPay!\n\n'
            '🚀 Автовыдача товаров\n'
            '📈 Автоподнятие лотов\n'
            '💬 Автоответ на сообщения\n'
            '⚙️ Команды, хуки, форматтеры, чего тут только нет (мне было лень вспоминать)\n'
            '🧩 Модульная система, поддержка плагинов\n'
            '🔧 Множество настроек и кастомизация\n\n'
            '…и многое другое, чтобы полностью контролировать продажи и экономить время!\n\n'
            '💻 Github: https://github.com/funpayhub/funpayhub\n'
            '💬 Чат проекта: https://t.me/funpay_hub',
        )

        await hub.telegram.bot.set_my_short_description(
            '🤖 Лучший бот для автоматизации продаж на FunPay!\n'
            '💬 Чат проекта: https://t.me/funpay_hub',
        )
