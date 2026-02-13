from __future__ import annotations

from typing import TYPE_CHECKING
from asyncio import Lock

from aiogram import Router
from aiogram.types import CallbackQuery

from funpayhub import exit_codes
from funpayhub.updater import check_updates, install_update, download_update

from funpayhub.app.telegram.ui.ids import MenuIds

from . import callbacks as cbs
from .ui import UpdateMenuContext, InstallUpdateMenuContext


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui.registry import UIRegistry as UI

    from funpayhub.app.main import FunPayHub as FPH


router = r = Router(name='fph:updates')
updating_lock = Lock()


@r.callback_query(cbs.CheckForUpdates.filter())
async def check_for_updates(query: CallbackQuery, tg_ui: UI, hub: FPH, translater: Tr) -> None:
    try:
        update = await check_updates(hub.properties.version.value)
    except:
        await query.answer(
            translater.translate(
                '❌ Произошла ошибка при получении данных об обновлениях.\nПодробности в лог файле.',
            ),
            show_alert=True,
        )
        return

    await UpdateMenuContext(
        menu_id=MenuIds.update,
        trigger=query,
        update_info=update,
    ).build_and_answer(tg_ui, query.message)
    await query.answer()


@r.callback_query(cbs.DownloadUpdate.filter())
async def download_upd(
    query: CallbackQuery,
    tg_ui: UI,
    callback_data: cbs.DownloadUpdate,
    hub: FPH,
    translater: Tr,
) -> None:
    if updating_lock.locked():
        await query.answer(
            translater.translate(
                '❌ Процесс установки обновления уже запущен. Пожалуйста, подождите.',
            ),
            show_alert=True,
        )
        return

    async with updating_lock:
        try:
            await download_update(callback_data.url)
        except:
            await query.answer(
                translater.translate(
                    '❌ Произошла ошибка при скачивании обновления.\nПодробности в лог файле.',
                ),
                show_alert=True,
            )
            return

    await InstallUpdateMenuContext(
        menu_id=MenuIds.install_update,
        trigger=query,
        instance_id=hub.instance_id,
    ).build_and_apply(tg_ui, query.message)


@r.callback_query(cbs.InstallUpdate.filter())
async def install_upd(
    query: CallbackQuery,
    callback_data: cbs.InstallUpdate,
    hub: FPH,
    translater: Tr,
) -> None:
    if callback_data.instance_id != hub.instance_id:
        await query.answer(
            translater.translate('❌ Эта кнопка устарела :(\nОткройте меню заного.'),
            show_alert=True,
        )
        return

    if updating_lock.locked():
        await query.answer(
            translater.translate(
                '❌ Процесс установки обновления уже запущен. Пожалуйста, подождите.',
            ),
            show_alert=True,
        )
        return

    async with updating_lock:
        try:
            install_update('.update.zip')
        except:
            await query.answer(
                translater.translate(
                    '❌ Произошла ошибка при распаковке обновления.\nПодробнее в лог файле.',
                ),
                show_alert=True,
            )
            return

    await query.message.edit_text(translater.translate('⏳ Установка обновления ...'))
    await hub.shutdown(exit_codes.UPDATE)
