from __future__ import annotations

import html
import shutil
import asyncio
from typing import TYPE_CHECKING

from aiogram import Bot, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.plugins import PluginManager
from funpayhub.app.telegram import states
from funpayhub.lib.plugins.installers import (
    HTTPSPluginInstaller,
    AiogramPluginInstaller,
    PluginInstallationError,
)


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


@router.callback_query(
    cbs.InstallPlugin.filter(), lambda _, callback_data: callback_data.mode == 1
)
async def install_plugin(
    query: CallbackQuery,
    state: FSMContext,
    translater: Translater,
    callback_data: cbs.InstallPlugin,
    plugin_manager: PluginManager,
):
    if plugin_manager.installation_lock.locked():
        await query.answer(translater.translate('$plugin_installation_locked'), show_alert=True)
        return

    msg = await query.message.answer(
        text=translater.translate('$install_plugin_from_zip_text'),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=translater.translate('$clear_state'),
                        callback_data=cbs.Clear(delete_message=True).pack(),
                    )
                ],
            ],
        ),
    )

    data = states.InstallingZipPlugin(
        message=msg,
        callback_query_obj=query,
        callback_data=callback_data,
    )
    await state.set_state(data.identifier)
    await state.set_data({'data': data})
    await query.answer()


@router.message(StateFilter(states.InstallingZipPlugin.identifier))
async def install_plugin(
    message: Message,
    plugin_manager: PluginManager,
    translater: Translater,
    tg_bot: Bot,
    state: FSMContext,
):
    if plugin_manager.installation_lock.locked():
        await message.reply(translater.translate('$plugin_installation_locked'))

    args = ()
    kwargs = {}
    if message.document:
        installer = AiogramPluginInstaller
        source = message.document.file_id
        kwargs = {'bot': tg_bot}
    elif message.reply_to_message and message.reply_to_message.document:
        installer = AiogramPluginInstaller
        source = message.reply_to_message.document.file_id
        kwargs = {'bot': tg_bot}
    elif message.text:
        installer = HTTPSPluginInstaller
        source = message.text
    else:
        await message.reply(translater.translate('$install_plugin_from_zip_text'))
        return

    data: states.InstallingZipPlugin = (await state.get_data())['data']
    await state.clear()
    await data.message.delete()

    async def task():
        try:
            await plugin_manager.install_plugin_from_source(installer, source, *args, **kwargs)
        except PluginInstallationError as e:
            await message.answer(
                translater.translate('$plugin_installation_error')
                + '\n'
                + html.escape(translater.translate(e.args[0]) % e.args[1:]),
            )
            return

        await message.answer(translater.translate('$plugin_installed_successfully'))

    asyncio.create_task(task())
