from __future__ import annotations

from typing import TYPE_CHECKING
from contextlib import suppress

from aiogram import Router
from aiogram.filters import Command
from aiogram.exceptions import AiogramError

from funpayhub import exit_codes
from funpayhub.loggers import main as logger

from funpayhub.lib.translater import _en
from funpayhub.lib.base_app.telegram.utils import delete_message

from funpayhub.app.telegram import (
    states,
    callbacks as cbs,
)
from funpayhub.app.formatters import FormattersContext


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery
    from aiogram.fsm.context import FSMContext

    from funpayhub.lib.translater import Translater
    from funpayhub.lib.hub.text_formatters import FormattersRegistry

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.app.funpay.main import FunPay


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


@router.callback_query(cbs.SendTemplate.filter())
async def send_template(
    query: CallbackQuery,
    properties: FPHProps,
    fp: FunPay,
    callback_data: cbs.SendTemplate,
    translater: Translater,
    fp_formatters: FormattersRegistry,
    state: FSMContext,
) -> None:
    data = None
    try:
        data = await states.SendingFunpayMessage.get(state)
    except RuntimeError:
        pass

    if data is not None:
        await state.clear()

    try:
        template = properties.message_templates.value[callback_data.index]
    except IndexError:
        await query.answer(
            translater.translate('❌ Быстрое сообщение {index} не найдено.').format(
                index=callback_data.index,
            ),
            show_alert=True,
        )
        return

    context = FormattersContext()

    try:
        text = await fp_formatters.format_text(template, context)
    except Exception:
        logger.error(
            _en('An error occurred while formatting fast message %s.'),
            template,
            exc_info=True,
        )
        await query.answer(
            translater.translate('❌ Не удалось форматировать сообщение. Подробности в логах.'),
            show_alert=True,
        )
        return

    try:
        await fp.send_messages_stack(text, chat_id=callback_data.to, automatic_message=False)
    except Exception:
        logger.error(
            _en('An error occurred while sending fast message %s.'),
            template,
            exc_info=True,
        )
        await query.answer(
            translater.translate('❌ Не удалось отправить сообщение. Подробности в логах.'),
        )
        return

    await query.answer(translater.translate('✅ Сообщение отправлено.'))
    if data is not None:
        delete_message(data.message)
