from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

import exit_codes

from funpayhub.lib.translater import _

from . import callbacks as cbs


if TYPE_CHECKING:
    from aiogram.types import CallbackQuery

    from funpayhub.lib.translater import Translater

    from funpayhub.app.main import FunPayHub


router = Router(name='fph:system')


@router.callback_query(cbs.ShutDown.filter())
async def shutdown(
    query: CallbackQuery,
    hub: FunPayHub,
    callback_data: cbs.ShutDown,
    translater: Translater,
) -> None:
    texts = {
        exit_codes.SHUTDOWN: _('⏹️ Выключаюсь...'),
        exit_codes.RESTART: _('♻️ Перезапускаюсь...'),
        exit_codes.RESTART_SAFE: _('♻️ Перезапускаюсь в безопасный режим...'),
        exit_codes.RESTART_NON_SAFE: _('♻️ Перезапускаюсь в стандартный режим...'),
    }
    text = texts.get(callback_data.exit_code, _('⏹️ Выключаюсь...'))

    try:
        await query.answer(text=translater.translate(text), show_alert=True)
    except:
        pass

    await hub.shutdown(callback_data.exit_code)
