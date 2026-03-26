from __future__ import annotations


__all__ = [
    'PluginMenuContext',
    'RepoInfoMenuContext',
    'RepoPluginInfoMenuContext',
    'PluginsListMenuBuilder',
    'PluginInfoMenuBuilder',
    'ReposListMenuBuilder',
    'RepoInfoMenuBuilder',
]

import html
from typing import TYPE_CHECKING
from html import escape

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import (
    Menu,
    Button,
    MenuBuilder,
    MenuContext,
    KeyboardBuilder,
)
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from funpayhub.app.telegram.ui.ids import MenuIds

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.plugin import PluginManager
    from funpayhub.lib.plugin.repository.manager import RepositoriesManager

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties as FPHProps


ru = translater.translate


class PluginMenuContext(MenuContext):
    plugin_id: str


class RepoInfoMenuContext(MenuContext):
    repo_id: str


class RepoPluginInfoMenuContext(MenuContext):
    repo_id: str
    plugin_id: str
    version: str | None = None


class PluginsListMenuBuilder(MenuBuilder, menu_id=MenuIds.plugins_list, context_type=MenuContext):
    async def build(self, ctx: MenuContext, plugin_manager: PluginManager) -> Menu:
        keyboard = KeyboardBuilder()
        for i in plugin_manager._plugins.values():
            prefix = '🔴' if i.manifest.plugin_id in plugin_manager.disabled_plugins else '🟢'
            if not i.plugin:
                prefix += '❌'
            prefix += ' '

            keyboard.add_callback_button(
                button_id=f'plugin_info:{i.manifest.plugin_id}',
                text=prefix + i.manifest.name,
                callback_data=OpenMenu(
                    menu_id=MenuIds.plugin_info,
                    context_data={'plugin_id': i.manifest.plugin_id},
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            )

        footer_keyboard = KeyboardBuilder()
        footer_keyboard.add_callback_button(
            button_id='open_installation_menu',
            text=ru('⤵ Установить'),
            callback_data=OpenMenu(
                menu_id=MenuIds.install_plugin,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        footer_keyboard.add_callback_button(
            button_id='open_repositories',
            text=ru('🗃 Репозитории'),
            callback_data=OpenMenu(
                menu_id=MenuIds.repositories_list,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        return Menu(
            main_text=ru('🧩 Плагины'),
            main_keyboard=keyboard,
            footer_keyboard=footer_keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )


class PluginInfoMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.plugin_info,
    context_type=PluginMenuContext,
):
    async def build(
        self,
        ctx: PluginMenuContext,
        plugin_manager: PluginManager,
        props: FPHProps,
    ) -> Menu:
        plugin = plugin_manager._plugins[ctx.plugin_id]
        man = plugin.manifest

        blocks = {
            'name': [],
            'info': [],
            'social': [],
            'description': [],
            'error': [],
        }

        keyboard = KeyboardBuilder()

        blocks['name'].append(f'🧩 <b><u>{escape(man.name)} v{man.plugin_version}</u></b>')
        blocks['info'].append(f'🆔 <b>ID: {man.plugin_id}</b>')

        if man.repo:
            blocks['info'].append(f'{ru("⬛ <b>Репозиторий</b>")}: {escape(man.repo)}')

        author_info = []
        if man.author:
            author = man.author
            if author.name:
                author_info.append(f'<b>{escape(author.name)}</b>')
            if author.website:
                author_info.append(f'<b><a href="{author.website}">{ru("🌐 Вебсайт")}</a></b>')

        if author_info:
            blocks['info'].append(f'{ru("👤 <b>Разработчик</b>")}: {" | ".join(author_info)}')

        if man.author and man.author.social:
            for name, link in man.author.social.items():
                blocks['social'].append(f'<b><i>{escape(name)}:</i> {escape(link)}</b>')

        if man.description:
            blocks['description'].append(
                escape(man.get_description(locale=props.general.language.real_value)),
            )

        if plugin.error:
            if isinstance(plugin.error, TranslatableException):
                error_text = plugin.error.format_args(translater.translate(plugin.error.message))
            else:
                error_text = 'Подробная информация об ошибке в лог файле.'

            blocks['error'].append(f'❌ Плагин не загружен.\n{error_text}')

        if plugin.properties:
            keyboard.add_callback_button(
                button_id='plugin_properties',
                text=ru('⚙️ Настройки'),
                callback_data=OpenMenu(
                    menu_id=MenuIds.props_node,
                    ui_history=ctx.as_ui_history(),
                    context_data={'entry_path': plugin.properties.path},
                ).pack(),
            )

        keyboard.add_callback_button(
            button_id='toggle_plugin_state',
            text=ru('🟢 Активировать')
            if man.plugin_id in plugin_manager.disabled_plugins
            else ru('🔴 Деактивировать'),
            callback_data=cbs.SetPluginStatus(
                plugin_id=man.plugin_id,
                status=man.plugin_id in plugin_manager.disabled_plugins,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        keyboard.add_callback_button(
            button_id='remove_plugin',
            text=ru('🗑️ Удалить'),
            callback_data=cbs.RemovePlugin(
                plugin_id=man.plugin_id,
                ui_history=ctx.ui_history,
            ).pack(),
        )

        return Menu(
            main_text='\n\n'.join('\n'.join(block) for block in blocks.values() if block),
            main_keyboard=keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )


class InstallPluginMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.install_plugin,
    context_type=MenuContext,
):
    async def build(self, ctx: MenuContext) -> Menu:
        menu = Menu(
            main_text=ru('<b>⤵ Выберите вариант установки плагина.</b>'),
            finalizer=StripAndNavigationFinalizer(),
        )

        menu.main_keyboard.add_callback_button(
            button_id='install_plugin:1',
            text=translater.translate('📦 Из ZIP архива'),
            callback_data=cbs.InstallPlugin(mode=1, ui_history=ctx.as_ui_history()).pack(),
        )
        return menu


class ReposListMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.repositories_list,
    context_type=MenuContext,
):
    async def build(self, ctx: MenuContext, repositories_manager: RepositoriesManager) -> Menu:
        menu = Menu(
            main_text=ru('🗃 <b><u>Репозитории</u></b>'),
            finalizer=StripAndNavigationFinalizer(),
        )

        if 'com.github.funpayhub.repo' in repositories_manager._repositories:
            repos = {
                'com.github.funpayhub.repo': repositories_manager._repositories[
                    'com.github.funpayhub.repo'
                ],
                **repositories_manager._repositories,
            }
        else:
            repos = repositories_manager._repositories

        for repo_id, repo in repos.items():
            menu.main_keyboard.add_callback_button(
                button_id=f'open_repository:{repo_id}',
                text=html.escape(repo.name),
                callback_data=OpenMenu(
                    menu_id=MenuIds.repository_info,
                    context_data={'repo_id': repo_id},
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            )

        menu.footer_keyboard.add_callback_button(
            button_id='add_repository',
            text=ru('➕ Добавить репозиторий'),
            callback_data=cbs.AddRepository(ui_history=ctx.as_ui_history()).pack(),
        )

        return menu


class RepoInfoMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.repository_info,
    context_type=RepoInfoMenuContext,
):
    async def build(
        self,
        ctx: RepoInfoMenuContext,
        repositories_manager: RepositoriesManager,
    ) -> Menu:
        repo = repositories_manager.repositories[ctx.repo_id]

        menu = Menu(
            header_text=f'<b><u>{html.escape(repo.name)}</u></b>',
            main_text=html.escape(repo.get_description(translater.current_language)),
            finalizer=StripAndNavigationFinalizer(),
        )

        for plugin_id, plugin in repo.plugins.items():
            menu.main_keyboard.add_callback_button(
                button_id=f'open_plugin_info:{plugin_id}',
                text=(
                    html.escape(plugin.name)
                    + (
                        f' by {html.escape(plugin.author.name)}'
                        if plugin.author and plugin.author.name
                        else ''
                    )
                ),
                callback_data=OpenMenu(
                    menu_id=MenuIds.repo_plugin_info,
                    context_data={'repo_id': ctx.repo_id, 'plugin_id': plugin_id},
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            )

        menu.footer_keyboard.add_callback_button(
            button_id='update_repo',
            text=ru('♻️ Обновить репозиторий'),
            callback_data=cbs.UpdateRepository(
                url=repo.url,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        return menu


class RepoPluginInfoMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.repo_plugin_info,
    context_type=RepoPluginInfoMenuContext,
):
    async def build(
        self,
        ctx: RepoPluginInfoMenuContext,
        repositories_manager: RepositoriesManager,
        hub: FunPayHub,
    ) -> Menu:
        menu = Menu(finalizer=StripAndNavigationFinalizer())

        repo = repositories_manager.repositories[ctx.repo_id]
        plugin = repo.plugins[ctx.plugin_id]

        blocks = {
            'name': [],
            'info': [],
            'social': [],
            'description': [],
        }

        blocks['name'].append(f'🧩 <b><u>{escape(plugin.name)}</u></b>')
        blocks['info'].append(f'🆔 <b>ID: {ctx.plugin_id}</b>')

        if plugin.repo:
            blocks['info'].append(f'{ru("⬛ <b>Репозиторий</b>")}: {escape(plugin.repo)}')

        author_info = []
        if plugin.author:
            author = plugin.author
            if author.name:
                author_info.append(f'<b>{escape(author.name)}</b>')
            if author.website:
                author_info.append(f'<b><a href="{author.website}">{ru("🌐 Вебсайт")}</a></b>')

        if author_info:
            blocks['info'].append(f'{ru("👤 <b>Разработчик</b>")}: {" | ".join(author_info)}')

        if plugin.author and plugin.author.social:
            for name, link in plugin.author.social.items():
                blocks['social'].append(f'<b><i>{escape(name)}:</i> {escape(link)}</b>')

        if plugin.description:
            blocks['description'].append(
                escape(plugin.get_description(locale=translater.current_language)),
            )

        menu.main_text = '\n\n'.join('\n'.join(block) for block in blocks.values() if block)

        latest = None
        for v, info in sorted(plugin.versions.items(), key=lambda x: x[0], reverse=True):
            if hub.version not in info.app_version:
                continue

            if latest is None:
                latest = v
            elif v > latest:
                latest = v

            menu.main_keyboard.add_row(
                Button.callback_button(
                    button_id=f'install_version:{v}',
                    text=f'⤵️ v{v}',
                    callback_data=cbs.InstallPluginFromURL(
                        url=info.url,
                        hash=info.hash,
                        ui_history=ctx.as_ui_history(),
                    ).pack(),
                ),
                Button.callback_button(
                    button_id=f'change_log:{v}',
                    text=ru('📃 Список изменений'),
                    callback_data='dummy',
                ),
            )

        if latest is not None:
            menu.footer_keyboard.add_callback_button(
                button_id='install_latest_version',
                text=ru('⤵️ Установить последнюю версию'),
                callback_data=cbs.InstallPluginFromURL(
                    url=plugin.versions[latest].url,
                    hash=plugin.versions[latest].hash,
                    ui_history=ctx.as_ui_history(),
                ).pack(),
            )

        return menu
