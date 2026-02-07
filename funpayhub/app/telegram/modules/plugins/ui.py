from __future__ import annotations


__all__ = [
    'PluginMenuContext',
    'PluginsListMenuBuilder',
    'PluginInfoMenuBuilder',
]


from typing import TYPE_CHECKING
from dataclasses import dataclass
from html import escape

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.telegram.ui import (
    Menu,
    Button,
    MenuBuilder,
    MenuContext as MenuCtx,
    KeyboardBuilder,
)
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from funpayhub.app.telegram.ui.ids import MenuIds

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.plugins import PluginManager
    from funpayhub.lib.translater import Translater as Tr

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


@dataclass(kw_only=True)
class PluginMenuContext(MenuCtx):
    plugin_id: str


class PluginsListMenuBuilder(MenuBuilder, menu_id=MenuIds.plugins_list, context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, plugin_manager: PluginManager, translater: Tr) -> Menu:
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
                    from_callback=ctx.callback_data,
                ).pack(),
            )

        footer_keyboard = KeyboardBuilder()
        footer_keyboard.add_callback_button(
            button_id='open_installation_menu',
            text=translater.translate('$install_plugin'),
            callback_data=OpenMenu(
                menu_id=MenuIds.install_plugin,
                from_callback=ctx.callback_data,
            ).pack(),
        )

        return Menu(
            main_text=translater.translate('$plugins_list'),
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
        translater: Tr,
        plugin_manager: PluginManager,
        properties: FPHProps,
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
            blocks['info'].append(f'{translater.translate("$plugin_repo")}: {escape(man.repo)}')

        author_info = []
        if man.author:
            author = man.author
            if author.name:
                author_info.append(f'<b>{escape(author.name)}</b>')
            if author.website:
                author_info.append(
                    f'<b><a href="{author.website}">{translater.translate("$plugin_author_website")}</a></b>',
                )

        if author_info:
            blocks['info'].append(
                f'{translater.translate("$plugin_author")}: {" | ".join(author_info)}',
            )

        if man.author and man.author.social:
            for name, link in man.author.social.items():
                blocks['social'].append(f'<b><i>{escape(name)}:</i> {escape(link)}</b>')

        if man.description:
            blocks['description'].append(
                escape(man.get_description(locale=properties.general.language.real_value)),
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
                text=translater.translate('$plugin_properties'),
                callback_data=OpenMenu(
                    menu_id=MenuIds.props_node,
                    from_callback=ctx.callback_data,
                    context_data={'entry_path': plugin.properties.path},
                ).pack(),
            )

        keyboard.add_callback_button(
            button_id='toggle_plugin_state',
            text=translater.translate('$activate_plugin')
            if man.plugin_id in plugin_manager.disabled_plugins
            else translater.translate('$deactivate_plugin'),
            callback_data=cbs.SetPluginStatus(
                plugin_id=man.plugin_id,
                status=man.plugin_id in plugin_manager.disabled_plugins,
                history=ctx.callback_data.history if ctx.callback_data else [],
            ).pack(),
        )

        keyboard.add_callback_button(
            button_id='remove_plugin',
            text=translater.translate('$remove_plugin'),
            callback_data=cbs.RemovePlugin(
                plugin_id=man.plugin_id,
                history=ctx.callback_data.history if ctx.callback_data else [],
            ).pack(),
        )

        return Menu(
            main_text='\n\n'.join('\n'.join(block) for block in blocks.values() if block),
            main_keyboard=keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )


class InstallPluginMenuBuilder(MenuBuilder, menu_id=MenuIds.install_plugin, context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, translater: Tr) -> Menu:
        kb = KeyboardBuilder()

        kb.add_rows(
            Button.callback_button(
                button_id='install_plugin:1',
                text=translater.translate('$install_plugin_from_zip'),
                callback_data=cbs.InstallPlugin(mode=1).pack(),
                row=True,
            ),
        )

        return Menu(
            main_text=translater.translate('$install_plugin_choice'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )
