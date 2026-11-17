from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import CallbackQuery as Query
from hubplatform.app.app import AppState
from hubplatform.runtime import ExitCodes
from hubplatform.telegram import Router

from dothub.loggers import telegram_component as logger

from . import callbacks as cbs


if TYPE_CHECKING:
    from hubplatform.app import HubPlatformApp


router = Router(name='app:telegram_component:main_menu')


STOP_MESSAGES: dict[int, str] = {
    ExitCodes.SHUTDOWN: '🛑 Выключаюсь',
    ExitCodes.RESTART: '🔄 Перезапускаюсь',
    ExitCodes.RESTART_SAFE: '🛡 Перезапускаюсь в безопасном режиме',
    ExitCodes.RESTART_NORMAL: '🔓 Перезапускаюсь в обычном режиме',
}
"""Exit codes allowed from the main menu and their answers."""


@router.callback_query(cbs.StopApp.filter())
async def stop_app(q: Query, cbd: cbs.StopApp, app: HubPlatformApp) -> None:
    message = STOP_MESSAGES.get(cbd.exit_code)
    if message is None:
        await q.answer()
        return

    if app.state is not AppState.RUNNING:
        await q.answer('⏳ Уже останавливаюсь')
        return

    exit_code = ExitCodes(cbd.exit_code)
    logger.info(
        'App stop requested from Telegram by user %s (exit code: %s).',
        q.from_user.id,
        exit_code.name,
    )
    await q.answer(message)
    app.stop(exit_code)
