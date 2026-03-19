from __future__ import annotations


__all__ = [
    'UpdateMenuContext',
    'InstallUpdateMenuContext',
    'UpdateMenuBuilder',
    'InstallUpdateMenuBuilder',
]


import html
from typing import TYPE_CHECKING

from funpayhub.updater import UpdateInfo

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import Menu, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from funpayhub.app.telegram.ui.ids import MenuIds

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub as FPH


ru = translater.translate


class UpdateMenuContext(MenuContext):
    update_info: UpdateInfo | None = None


class InstallUpdateMenuContext(MenuContext):
    instance_id: str


class UpdateMenuBuilder(MenuBuilder, menu_id=MenuIds.update, context_type=UpdateMenuContext):
    async def build(self, ctx: UpdateMenuContext) -> Menu:
        menu = Menu(finalizer=StripAndNavigationFinalizer())
        if ctx.update_info is None:
            menu.main_text = ru('<b>✅ Установлена последняя версия FunPay Hub.</b>')
            return menu

        desc = html.escape(ctx.update_info.description)
        if len(desc) > 3000:
            desc = (
                f'{desc[:3000]}...\n\n{ru("Полный список изменений")}'
                ': https://github.com/funpayhub/funpayhub/releases/latest'
            )

        menu.main_text = (
            f'{ru("<b>🔥 Доступно новое обновление</b>!")}\n\n'
            f'<b>{html.escape(ctx.update_info.title)}</b>\n\n'
            f'{desc}'
        )

        menu.main_keyboard.add_callback_button(
            button_id='download_update',
            text=ru('🔽 Скачать обновление'),
            callback_data=cbs.DownloadUpdate(
                url=ctx.update_info.url,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        return menu


class InstallUpdateMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.install_update,
    context_type=InstallUpdateMenuContext,
):
    async def build(self, ctx: InstallUpdateMenuContext, hub: FPH) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='install_update',
            text=ru('⏬ Установить обновление'),
            callback_data=cbs.InstallUpdate(instance_id=hub.instance_id).pack_compact(),
        )

        return Menu(
            main_text=ru('<b>✅ Обновление скачано.</b>'),
            main_keyboard=kb,
        )
