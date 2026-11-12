from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from aiogram.types import CallbackQuery as Query
from hubplatform.telegram import Router
from hubplatform.updates.exceptions import VersionDownloadInProgressError
from hubplatform.telegram.ui.session import MenuFrame

from dothub.loggers import telegram_component as logger

from . import callbacks as cbs
from .ui import UpdateStatus, UpdateMenuContext
from .menu_ids import UpdatesUIMenuIDs
from .versions import UPDATES_DIR


if TYPE_CHECKING:
    from aiogram import Bot
    from hubplatform.app import HubPlatformApp
    from hubplatform.updates import VersionsManager
    from hubplatform.telegram.ui import UIManager


router = Router(name='app:telegram_component:updates')

_download_tasks: set[asyncio.Task[Any]] = set()
"""Running downloads. A task is added right after creation, without awaits in between,
so it marks the download as started for the next click immediately."""


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


@router.callback_query(cbs.DownloadUpdate.filter())
async def download_update(
    q: Query,
    cbd: cbs.DownloadUpdate,
    versions_manager: VersionsManager,
    telegram_ui_manager: UIManager,
) -> None:
    # `is_downloading` also covers downloads started outside of this module.
    if _download_tasks or versions_manager.is_downloading(UPDATES_DIR):
        await q.answer('⏳ Обновление уже загружается')
        return

    status_shown = asyncio.Event()
    # Downloading may take a while, so it does not block the callback handler.
    task = asyncio.create_task(
        _download(
            cbd.version,
            cbd.session_id,
            q.bot,
            versions_manager,
            telegram_ui_manager,
            status_shown,
        ),
        name=f'app:updates:download:{cbd.version}',
    )
    _download_tasks.add(task)
    task.add_done_callback(_download_tasks.discard)

    try:
        await _set_status(telegram_ui_manager, cbd.session_id, q.bot, 'downloading')
    finally:
        status_shown.set()
    await q.answer()


async def _download(
    version: str,
    session_id: str,
    bot: Bot | None,
    versions_manager: VersionsManager,
    ui_manager: UIManager,
    status_shown: asyncio.Event,
) -> None:
    try:
        path = await versions_manager.download_version(version, UPDATES_DIR)
    except VersionDownloadInProgressError:
        logger.info('Update is already being downloaded, skipping download of %s.', version)
        status: UpdateStatus = 'available'
        path = None
    except Exception:
        logger.error('Unable to download update %s.', version, exc_info=True)
        status = 'download_failed'
        path = None
    else:
        logger.info('Update %s has been downloaded to %s.', version, path)
        status = 'downloaded'

    # Do not overwrite "downloading" status before it is even shown.
    await status_shown.wait()
    await _set_status(
        ui_manager,
        session_id,
        bot,
        status,
        downloaded_path=str(path) if path is not None else None,
    )


async def _set_status(
    ui_manager: UIManager,
    session_id: str,
    bot: Bot | None,
    status: UpdateStatus,
    downloaded_path: str | None = None,
) -> None:
    async with ui_manager.edit_session(session_id=session_id, bot=bot, rerender=True) as s:
        context = UpdateMenuContext.model_validate(s.current.context_fields)
        context = context.model_copy(update={'status': status, 'downloaded_path': downloaded_path})
        s.current = MenuFrame.from_menu_context(
            menu_id=UpdatesUIMenuIDs.update,
            menu_context=context,
        )
