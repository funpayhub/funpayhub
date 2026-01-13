from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Router
from aiogram.types import CallbackQuery

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.app.telegram.ui.builders.context import UpdateMenuContext, InstallUpdateMenuContext
from updater import check_updates, download_update, install_update
from exit_codes import UPDATE
import sys

from funpayhub.app.telegram.ui.ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.lib.translater import Translater


router = r = Router(name='fph:updates')


@r.callback_query(cbs.CheckForUpdates.filter())
async def check_for_updates(
    query: CallbackQuery,
    tg_ui: UIRegistry,
    data: dict[str, Any],
    hub: FunPayHub,
    translater: Translater,
):
    try:
        update = await check_updates(hub.properties.version.value)
    except:
        await query.answer(translater.translate('$error_fetching_updates'), show_alert=True)
        return

    ctx = UpdateMenuContext(
        menu_id=MenuIds.update,
        trigger=query,
        update_info=update,
    )

    menu = await tg_ui.build_menu(ctx, data | {'query': query})
    await menu.reply_to(query.message)
    await query.answer()


@r.callback_query(cbs.DownloadUpdate.filter())
async def download_upd(
    query: CallbackQuery,
    tg_ui: UIRegistry,
    data: dict[str, Any],
    callback_data: cbs.DownloadUpdate,
    hub: FunPayHub,
    translater: Translater,
):
    try:
        await download_update(callback_data.url)
    except:
        await query.answer(translater.translate('$error_downloading_update'), show_alert=True)
        return

    ctx = InstallUpdateMenuContext(
        menu_id=MenuIds.install_update,
        trigger=query,
        instance_id=hub.instance_id
    )

    menu = await tg_ui.build_menu(ctx, data | {'query': query})
    await menu.apply_to(query.message)


@r.callback_query(cbs.InstallUpdate.filter())
async def install_upd(
    query: CallbackQuery,
    callback_data: cbs.InstallUpdate,
    hub: FunPayHub,
    translater: Translater,
):
    if callback_data.instance_id != hub.instance_id:
        await query.answer(translater.translate('$wrong_update_instance_id'), show_alert=True)
        return

    try:
        install_update('.update.zip')
    except:
        await query.answer(translater.translate('$error_unpacking_update'), show_alert=True)
        return

    await query.message.edit_text(translater.translate('$installing_update'))
    sys.exit(UPDATE) # todo: shutdown
