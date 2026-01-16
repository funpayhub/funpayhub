from __future__ import annotations


__all__ = ['PluginsListMenuBuilder']


from typing import TYPE_CHECKING

from funpayhub.app.telegram import callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import Menu, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer
from funpayhub.app.telegram.ui.builders.context import PluginMenuContext
import html


if TYPE_CHECKING:
    from funpayhub.lib.plugins import PluginManager
    from funpayhub.app.properties import FunPayHubProperties


class PluginsListMenuBuilder(MenuBuilder):
    id = MenuIds.plugins_list
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        plugin_manager: PluginManager,
        translater: Translater,
    ) -> Menu:
        keyboard = KeyboardBuilder()
        for i in plugin_manager._plugins.values():
            prefix = '🔴' if i.manifest.plugin_id in plugin_manager.disabled_plugins else '🟢'
            if not i.plugin:
                prefix += '❌'
            prefix += ' '

            keyboard.add_callback_button(
                button_id=f'plugin_info:{i.manifest.plugin_id}',
                text=prefix + i.manifest.name,
                callback_data=cbs.OpenMenu(
                    menu_id=MenuIds.plugin_info,
                    context_data={
                        'plugin_id': i.manifest.plugin_id,
                    },
                    history=ctx.callback_data.as_history() if ctx.callback_data else []
                ).pack(),
            )

        return Menu(
            text=translater.translate('$plugins_list'),
            main_keyboard=keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )


class PluginInfoMenuBuilder(MenuBuilder):
    id = MenuIds.plugin_info
    context_type = PluginMenuContext

    async def build(
        self,
        ctx: PluginMenuContext,
        translater: Translater,
        plugin_manager: PluginManager,
        properties: FunPayHubProperties
    ) -> Menu:
        plugin = plugin_manager._plugins[ctx.plugin_id]
        manifest = plugin.manifest

        blocks = {
            'name': [],
            'info': [],
            'social': [],
            'description': []
        }

        keyboard = KeyboardBuilder()

        blocks['name'].append(
            f'🧩 <b><u>{html.escape(manifest.name)} v{manifest.plugin_version}</u></b>'
        )
        blocks['info'].append(f'🆔 <b>ID: {manifest.plugin_id}</b>')

        if manifest.repo:
            blocks['info'].append(
                f'{translater.translate("$plugin_repo")}: {html.escape(manifest.repo)}'
            )

        author_info = []
        if manifest.author:
            author = manifest.author
            if author.name:
                author_info.append(f'<b>{html.escape(author.name)}</b>')
            if author.website:
                author_info.append(f'<b><a href="{author.website}">{translater.translate("$plugin_author_website")}</a></b>')

        if author_info:
            blocks['info'].append(
                f'{translater.translate("$plugin_author")}: {" | ".join(author_info)}'
            )

        if manifest.author and manifest.author.social:
            for name, link in manifest.author.social.items():
                blocks['social'].append(
                    f'<b><i>{html.escape(name)}:</i> {html.escape(link)}</b>'
                )

        if manifest.description:
            blocks['description'].append(
                html.escape(manifest.get_description(locale=properties.general.language.real_value))
            )

        text = ''
        for block in blocks.values():
            if not block:
                continue

            text += '\n'.join(block) + '\n\n'

        text = text.strip()

        if plugin.properties:
            keyboard.add_callback_button(
                button_id='plugin_properties',
                text=translater.translate('$plugin_properties'),
                callback_data=cbs.OpenEntryMenu(
                    path=plugin.properties.path,
                    history=ctx.callback_data.as_history() if ctx.callback_data else [],
                ).pack()
            )

        keyboard.add_callback_button(
            button_id='toggle_plugin_state',
            text=translater.translate('$activate_plugin') if manifest.plugin_id in plugin_manager.disabled_plugins else translater.translate('$deactivate_plugin'),
            callback_data=cbs.SetPluginStatus(
                plugin_id=manifest.plugin_id,
                status=manifest.plugin_id in plugin_manager.disabled_plugins,
                history=ctx.callback_data.history if ctx.callback_data else []
            ).pack(),
        )

        keyboard.add_callback_button(
            button_id='remove_plugin',
            text=translater.translate('$remove_plugin'),
            callback_data=cbs.RemovePlugin(
                plugin_id=manifest.plugin_id,
                history=ctx.callback_data.history if ctx.callback_data else []
            ).pack()
        )

        return Menu(
            text = text,
            main_keyboard=keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )
