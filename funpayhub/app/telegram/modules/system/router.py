from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

import exit_codes

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
