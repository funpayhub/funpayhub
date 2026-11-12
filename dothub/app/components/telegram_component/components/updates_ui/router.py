from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from aiogram.types import CallbackQuery as Query
from hubplatform.runtime import ExitCodes
from hubplatform.telegram import Router
from hubplatform.updates.exceptions import VersionManagerError
from hubplatform.telegram.ui.session import MenuFrame

from dothub.loggers import telegram_component as logger

from . import callbacks as cbs
from .ui import UpdateStatus, UpdateMenuContext
from .menu_ids import UpdatesUIMenuIDs


if TYPE_CHECKING:
    from aiogram import Bot
    from hubplatform.app import HubPlatformApp
    from hubplatform.updates import InstallStage, VersionsManager, ReleaseInstaller
    from hubplatform.telegram.ui import UIManager


router = Router(name='app:telegram_component:updates')

MAX_ERROR_LENGTH = 300
"""Installation errors (e.g. uv output) are cut in the menu, the full one is in logs."""

_install_tasks: set[asyncio.Task[Any]] = set()
"""Running installations. A task is added right after creation, without awaits in between,
so it marks the installation as started for the next click immediately."""


@router.callback_query(cbs.CheckForUpdates.filter())
async def check_for_updates(
    q: Query,
    app: HubPlatformApp,
    versions_manager: VersionsManager,
    telegram_ui_manager: UIManager,
) -> None:
    try:
        versions = await versions_manager.get_versions(from_=app.version)
        if not versions:
            await q.answer('✅ Установлена последняя версия')
            return
        latest = await versions_manager.get_version_info(versions[0])
    except Exception:
        logger.error('Unable to check for updates.', exc_info=True)
        await q.answer('❌ Не удалось проверить обновления', show_alert=True)
        return

    await q.answer()
    await telegram_ui_manager.open_menu(
        menu_id=UpdatesUIMenuIDs.update,
        context=UpdateMenuContext(
            version=str(latest.version),
            notes=latest.notes,
            skipped_versions=[str(i) for i in versions[1:]],
        ),
        environment=q,
    )


@router.callback_query(cbs.InstallUpdate.filter())
async def install_update(
    q: Query,
    cbd: cbs.InstallUpdate,
    release_installer: ReleaseInstaller | None,
    telegram_ui_manager: UIManager,
) -> None:
    if release_installer is None:
        await q.answer('❌ FunPay Hub запущен без лаунчера', show_alert=True)
        return
    if _install_tasks or release_installer.is_installing:
        await q.answer('⏳ Обновление уже устанавливается')
        return

    status_shown = asyncio.Event()
    # Installation takes a while, so it does not block the callback handler.
    task = asyncio.create_task(
        _install(
            cbd.version,
            cbd.session_id,
            q.bot,
            release_installer,
            telegram_ui_manager,
            status_shown,
        ),
        name=f'app:updates:install:{cbd.version}',
    )
    _install_tasks.add(task)
    task.add_done_callback(_install_tasks.discard)

    try:
        await _set_status(telegram_ui_manager, cbd.session_id, q.bot, 'installing')
    finally:
        status_shown.set()
    await q.answer()


@router.callback_query(cbs.ApplyUpdate.filter())
async def apply_update(
    q: Query,
    cbd: cbs.ApplyUpdate,
    app: HubPlatformApp,
    release_installer: ReleaseInstaller | None,
    telegram_ui_manager: UIManager,
) -> None:
    if release_installer is None:
        await q.answer('❌ FunPay Hub запущен без лаунчера', show_alert=True)
        return

    try:
        release_installer.stage(cbd.version)
    except Exception:
        logger.error('Unable to stage update %s.', cbd.version, exc_info=True)
        await q.answer('❌ Обновление не установлено, установите его заново', show_alert=True)
        await _set_status(telegram_ui_manager, cbd.session_id, q.bot, 'available')
        return

    logger.info('Restarting to update to %s.', cbd.version)
    await q.answer('🔄 Перезапускаюсь')
    try:
        await _set_status(telegram_ui_manager, cbd.session_id, q.bot, 'restarting')
    except Exception:
        logger.warning('Unable to show restarting status.', exc_info=True)
    app.stop(ExitCodes.UPDATE)


async def _install(
    version: str,
    session_id: str,
    bot: Bot | None,
    installer: ReleaseInstaller,
    ui_manager: UIManager,
    status_shown: asyncio.Event,
) -> None:
    async def on_stage(stage: InstallStage) -> None:
        await status_shown.wait()
        await _set_status(ui_manager, session_id, bot, 'installing', stage=stage)

    error: str | None = None
    try:
        await installer.install(version, on_stage=on_stage)
    except VersionManagerError as e:
        logger.error('Unable to install update %s.', version, exc_info=True)
        status: UpdateStatus = 'install_failed'
        error = str(e)
        if e.__cause__ is not None:
            error += f' ({str(e.__cause__)[:MAX_ERROR_LENGTH]})'
    except Exception:
        logger.error('Unable to install update %s.', version, exc_info=True)
        status = 'install_failed'
    else:
        logger.info('Update %s has been installed.', version)
        status = 'installed'

    # Do not overwrite "installing" status before it is even shown.
    await status_shown.wait()
    await _set_status(ui_manager, session_id, bot, status, error=error)


async def _set_status(
    ui_manager: UIManager,
    session_id: str,
    bot: Bot | None,
    status: UpdateStatus,
    stage: InstallStage | None = None,
    error: str | None = None,
) -> None:
    async with ui_manager.edit_session(session_id=session_id, bot=bot, rerender=True) as s:
        context = UpdateMenuContext.model_validate(s.current.context_fields)
        context = context.model_copy(update={'status': status, 'stage': stage, 'error': error})
        s.current = MenuFrame.from_menu_context(
            menu_id=UpdatesUIMenuIDs.update,
            menu_context=context,
        )
