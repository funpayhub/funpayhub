from __future__ import annotations

import html
import shutil
from typing import TYPE_CHECKING, Any

from aiogram import Bot, Router

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.translater import translater
from funpayhub.lib.base_app.telegram import utils
from funpayhub.lib.plugin.installers import (
    HTTPSPluginInstaller,
    AiogramPluginInstaller,
    PluginInstallationError,
)
from funpayhub.lib.plugin.repository.types import PluginsRepository
from funpayhub.lib.plugin.repository.loaders import URLRepositoryLoader

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import StateUIContext

from . import (
    ui,
    states,
    callbacks as cbs,
)


if TYPE_CHECKING:
    from aiogram.types import (
        Message,
        CallbackQuery as Query,
    )
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.lib.plugin import PluginManager
    from funpayhub.lib.telegram.ui import UIRegistry as UI
    from funpayhub.lib.plugin.repository.manager import RepositoriesManager

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


router = r = Router(name='fph:plugins')
ru = translater.translate


@router.callback_query(cbs.SetPluginStatus.filter())
async def set_plugin_status(
    q: Query,
    plugin_manager: PluginManager,
    cbd: cbs.SetPluginStatus,
    props: FPHProps,
) -> Any:
    if cbd.plugin_id not in plugin_manager._plugins:
        return q.answer(ru('❌ Плагин не найден.'), show_alert=True)

    if cbd.status and cbd.plugin_id not in plugin_manager.disabled_plugins:
        return q.answer(ru('❌ Плагин уже активирован.'), show_alert=True)

    if not cbd.status and cbd.plugin_id in plugin_manager.disabled_plugins:
        return q.answer(translater.translate('❌ Плагин уже деактивирован.'), show_alert=True)

    if cbd.status:
        await plugin_manager.enable_plugin(plugin=cbd.plugin_id)
        await props.plugin_properties.disabled_plugins.remove_item(cbd.plugin_id)
    else:
        await plugin_manager.disable_plugin(plugin=cbd.plugin_id)
        await props.plugin_properties.disabled_plugins.add_item(cbd.plugin_id)

    text = ru('✅ Плагин активирован.' if cbd.status else '✅ Плагин деактивирован.')
    text += '\n' + ru('🔃 Чтобы изменения вступили в силу, перезапустите FunPay Hub.')
    return q.answer(text, show_alert=True)


@router.callback_query(cbs.RemovePlugin.filter())
async def set_plugin_status(q: Query, plugin_manager: PluginManager, cbd: cbs.RemovePlugin) -> Any:
    # todo: move logic to plugin manager
    if cbd.plugin_id not in plugin_manager._plugins:
        return q.answer(ru('❌ Плагин не найден.'), show_alert=True)

    plugin = plugin_manager._plugins[cbd.plugin_id]
    shutil.rmtree(plugin.path, ignore_errors=True)
    del plugin_manager._plugins[cbd.plugin_id]

    return q.answer(
        ru('✅ Плагин удален.')
        + '\n'
        + ru('🔃 Чтобы изменения вступили в силу, перезапустите FunPay Hub.'),
        show_alert=True,
    )


@router.callback_query(cbs.InstallPlugin.filter(), lambda _, cbd: cbd.mode == 1)
async def install_plugin(
    q: Query,
    state: FSM,
    cbd: cbs.InstallPlugin,
    plugin_manager: PluginManager,
) -> Any:
    if plugin_manager.installation_lock.locked():
        return q.answer(
            ru(
                '❌ В данный момент уже устанавливается какой-то плагин.\n'
                'Дождитесь окончания текущей установки и повторите попытку.',
            ),
            show_alert=True,
        )

    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        trigger=q,
        text=ru(
            'Пришлите или перешлите сообщение с '
            'ZIP архивом плагина / ссылкой на ZIP архив плагина.',
        ),
        ui_history=cbd.ui_history,
    ).answer_to()

    await states.InstallingZipPlugin(query=q, state_message=msg).set(state)
    await q.answer()


@router.message(states.InstallingZipPlugin.filter())
async def install_plugin(
    m: Message,
    plugin_manager: PluginManager,
    tg_bot: Bot,
    state: FSM,
) -> Any:
    if plugin_manager.installation_lock.locked():
        return m.reply(
            ru(
                '❌ В данный момент уже устанавливается какой-то плагин.\n'
                'Дождитесь окончания текущей установки и повторите попытку.',
            ),
        )

    args = ()
    kwargs = {}
    if m.document:
        installer, source, kwargs = AiogramPluginInstaller, m.document.file_id, {'bot': tg_bot}
    elif m.reply_to_message and m.reply_to_message.document:
        installer = AiogramPluginInstaller
        source = m.reply_to_message.document.file_id
        kwargs = {'bot': tg_bot}
    elif m.text:
        installer, source = HTTPSPluginInstaller, m.text
    else:
        return m.reply(
            ru(
                'Пришлите или перешлите сообщение с '
                'ZIP архивом плагина / ссылкой на ZIP архив плагина.',
            ),
        )

    data = await states.InstallingZipPlugin.clear(state)
    utils.delete_message(data.state_message)

    try:
        await plugin_manager.install_plugin_from_source(installer, source, *args, **kwargs)
    except PluginInstallationError as e:
        return m.answer(
            ru('Не удалось установить плагин.') + '\n' + html.escape(ru(e.message) % e.args),
        )

    return m.answer(ru('<b>🧩 Плагин успешно установлен!</b>'))


# Repos
@router.callback_query(cbs.AddRepository.filter())
async def activate_add_repository_state(q: Query, state: FSM) -> None:
    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        trigger=q,
        text=ru('<b>🔗 Пришлите ссылку на репозиторий.</b>'),
    ).answer_to()

    await states.AddingRepository(query=q, state_message=msg).set(state)


@router.message(states.AddingRepository.filter(), lambda msg: msg.text)
async def add_repo(m: Message, state: FSM, repositories_manager: RepositoriesManager) -> Any:
    data = await states.AddingRepository.get(state)
    await states.AddingRepository.clear(state)
    utils.delete_message(data.state_message)

    try:
        repo = await URLRepositoryLoader(url=m.text).load()
        repositories_manager.register_repository(repo)
    except Exception as e:
        msg = ru('<b>❌ Не удалось установить репозиторий.</b>')
        if isinstance(e, TranslatableException):
            msg += '\n\n' + e.format_args(translater.translate(e.message))
        else:
            msg += '\n\n' + ru('Подробности в логах.')

        return m.reply(msg)

    await ui.RepoInfoMenuContext(
        menu_id=MenuIds.repository_info,
        trigger=m,
        repo_id=repo.id,
        ui_history=data.ui_history,
    ).answer_to()


@router.callback_query(cbs.UpdateRepository.filter())
async def update_repository(
    q: Query,
    cbd: cbs.UpdateRepository,
    repositories_manager: RepositoriesManager,
    tg_ui: UI,
):
    try:
        repository = await PluginsRepository.from_url(url=cbd.url)
    except Exception as e:
        text = ru('<b>❌ Произошла ошибка при получении репозитория.</b>')
        if isinstance(e, TranslatableException):
            text += '\n\n' + e.format_args(translater.translate(e.message))
        else:
            text += '\n\n' + ru('<b>Подробности в логах.</b>')
        return q.answer(text, show_alert=True)

    try:
        repositories_manager.register_repository(repository, overwrite=True, save=True)
    except Exception as e:
        text = ru('<b>❌ Произошла ошибка при сохранении репозитория.</b>')
        if isinstance(e, TranslatableException):
            text += '\n\n' + e.format_args(translater.translate(e.message))
        else:
            text += '\n\n' + ru('<b>Подробности в логах.</b>')
        return q.answer(text, show_alert=True)

    await q.answer(ru('✅ Репозиторий обновлен.'), show_alert=True)
    await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to()


@router.callback_query(cbs.InstallPluginFromURL.filter())
async def install_plugin_from_url(
    q: Query,
    cbd: cbs.InstallPluginFromURL,
    plugin_manager: PluginManager,
):
    await q.answer()
    await q.message.answer(ru('<b>🧩 Загружаю плагин {url} .</b>', url=cbd.url))
    try:
        await plugin_manager.install_plugin_from_source(
            HTTPSPluginInstaller,
            cbd.url,
            overwrite=True,
            plugin_hash=cbd.hash,
        )
    except Exception as e:
        text = ru('<b>❌ Ошибка установки плагина {url} .</b>', url=cbd.url)
        if isinstance(e, TranslatableException):
            text += '\n\n' + e.format_args(translater.translate(e.message))
        else:
            text += '\n\n' + ru('<b>Подробности в логах.</b>')

        return q.message.answer(text)

    await q.message.answer(ru('<b>✅ Плагин установлен.\n\nПерезапустите FunPay Hub.</b>'))
