from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Router

from funpayhub import exit_codes

from funpayhub.lib.translater import translater

from . import callbacks as cbs


if TYPE_CHECKING:
    from aiogram.types import CallbackQuery as Query

    from funpayhub.app.main import FunPayHub as FPH


router = Router(name='fph:system')
ru = translater.translate


@router.callback_query(cbs.ShutDown.filter())
async def shutdown(q: Query, hub: FPH, cbd: cbs.ShutDown) -> Any:
    texts = {
        exit_codes.SHUTDOWN: ru('⏹️ Выключаюсь...'),
        exit_codes.RESTART: ru('♻️ Перезапускаюсь...'),
        exit_codes.RESTART_SAFE: ru('♻️ Перезапускаюсь в безопасный режим...'),
        exit_codes.RESTART_NON_SAFE: ru('♻️ Перезапускаюсь в стандартный режим...'),
    }
    text = texts.get(cbd.exit_code, ru('⏹️ Выключаюсь...'))

    try:
        await q.answer(text=translater.translate(text), show_alert=True)
    except:
        pass

    await hub.shutdown(cbd.exit_code)
