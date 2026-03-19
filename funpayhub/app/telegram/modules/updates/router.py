from __future__ import annotations

from typing import TYPE_CHECKING, Any
from asyncio import Lock

from aiogram import Router

from funpayhub import exit_codes
from funpayhub.updater import check_updates, install_update, download_update

from funpayhub.lib.translater import translater

from funpayhub.app.telegram.ui.ids import MenuIds

from . import callbacks as cbs
from .ui import UpdateMenuContext, InstallUpdateMenuContext


if TYPE_CHECKING:
    from aiogram.types import CallbackQuery as Query

    from funpayhub.app.main import FunPayHub as FPH


router = r = Router(name='fph:updates')
ru = translater.translate
updating_lock = Lock()


@r.callback_query(cbs.CheckForUpdates.filter())
async def check_for_updates(q: Query, hub: FPH) -> Any:
    try:
        update = await check_updates(hub.properties.version.value)
    except:
        return q.answer(
            ru('❌ Ошибка получения данных обновления.\nПодробности в лог файле.'),
            show_alert=True,
        )

    await UpdateMenuContext(menu_id=MenuIds.update, trigger=q, update_info=update).answer_to()


@r.callback_query(cbs.DownloadUpdate.filter())
async def download_upd(q: Query, cbd: cbs.DownloadUpdate, hub: FPH) -> Any:
    if updating_lock.locked():
        return q.answer(
            ru('❌ Процесс установки обновления уже запущен. Пожалуйста, подождите.'),
            show_alert=True,
        )

    async with updating_lock:
        try:
            await download_update(cbd.url)
        except:
            return q.answer(
                ru('❌ Ошика скачивания обновления.\nПодробности в лог файле.'),
                show_alert=True,
            )

    await InstallUpdateMenuContext(
        menu_id=MenuIds.install_update,
        trigger=q,
        instance_id=hub.instance_id,
    ).apply_to()


@r.callback_query(cbs.InstallUpdate.filter())
async def install_upd(query: Query, cbd: cbs.InstallUpdate, hub: FPH) -> Any:
    if cbd.instance_id != hub.instance_id:
        return query.answer(
            ru('❌ Эта кнопка устарела :(\nОткройте меню заного.'), show_alert=True
        )

    if updating_lock.locked():
        return query.answer(
            ru('❌ Процесс установки обновления уже запущен. Пожалуйста, подождите.'),
            show_alert=True,
        )

    async with updating_lock:
        try:
            install_update('.update.zip')
        except:
            return query.answer(
                ru('❌ Ошибка распаковки обновления.\nПодробнее в лог файле.'),
                show_alert=True,
            )

    await query.message.edit_text(ru('<b>⏳ Установка обновления ...</b>'))
    await hub.shutdown(exit_codes.UPDATE)
