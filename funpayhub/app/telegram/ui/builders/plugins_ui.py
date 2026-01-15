from __future__ import annotations


__all__ = ['PluginsListMenuBuilder']


from typing import TYPE_CHECKING

from funpayhub.app.telegram import callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import Menu, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer


if TYPE_CHECKING:
    from funpayhub.lib.plugins import PluginManager


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
            keyboard.add_callback_button(
                button_id=f'plugin_info:{i.manifest.plugin_id}',
                text=i.manifest.name,
                callback_data=cbs.OpenPluginInfo(plugin_id=i.manifest.plugin_id).pack(),
            )

        return Menu(
            text=translater.translate('$plugins_list'),
            main_keyboard=keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )
