from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.types import CallbackQuery

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.plugins import PluginManager


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater


router = r = Router(name='fph:plugins')


@router.callback_query(cbs.SetPluginStatus.filter())
async def set_plugin_status(
    query: CallbackQuery,
    plugin_manager: PluginManager,
    translater: Translater,
    callback_data: cbs.SetPluginStatus,
) -> None:
    if callback_data.plugin_id not in plugin_manager._plugins:
        await query.answer(translater.translate('$plugin_not_found'), show_alert=True)
        return

    if callback_data.status and callback_data.plugin_id not in plugin_manager.disabled_plugins:
        await query.answer(translater.translate('$plugin_already_enabled'), show_alert=True)
        return

    if not callback_data.status and callback_data.plugin_id in plugin_manager.disabled_plugins:
        await query.answer(translater.translate('$plugin_already_disabled'), show_alert=True)
        return

    if callback_data.status:
        await plugin_manager.enable_plugin(plugin=callback_data.plugin_id)
    else:
        await plugin_manager.disable_plugin(plugin=callback_data.plugin_id)

    text = translater.translate('$plugin_enabled' if callback_data.status else '$plugin_disabled')
    text += '\n' + translater.translate('$restart_required')

    await query.answer(text, show_alert=True)


@router.callback_query(cbs.RemovePlugin.filter())
async def set_plugin_status(
    query: CallbackQuery,
    plugin_manager: PluginManager,
    translater: Translater,
    callback_data: cbs.RemovePlugin,
):
    # todo: move logic to plugin manager
    if callback_data.plugin_id not in plugin_manager._plugins:
        await query.answer(translater.translate('$plugin_not_found'), show_alert=True)
        return

    plugin = plugin_manager._plugins[callback_data.plugin_id]
    shutil.rmtree(plugin.path, ignore_errors=True)
    del plugin_manager._plugins[callback_data.plugin_id]

    await query.answer(
        translater.translate('$plugin_removed') + '\n' + translater.translate('$restart_required'),
        show_alert=True,
    )
