from __future__ import annotations


__all__ = [
    'UpdateMenuContext',
    'InstallUpdateMenuContext',
    'UpdateMenuBuilder',
    'InstallUpdateMenuBuilder',
]


import html
from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.ui import Menu, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from funpayhub.app.telegram.ui.ids import MenuIds

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.updater import UpdateInfo

    from funpayhub.lib.translater import Translater as Tr

    from funpayhub.app.main import FunPayHub


@dataclass(kw_only=True)
class UpdateMenuContext(MenuContext):
    update_info: UpdateInfo | None = None


@dataclass(kw_only=True)
class InstallUpdateMenuContext(MenuContext):
    instance_id: str


class UpdateMenuBuilder(MenuBuilder, menu_id=MenuIds.update, context_type=UpdateMenuContext):
    async def build(self, ctx: UpdateMenuContext, translater: Tr) -> Menu:
        menu = Menu(finalizer=StripAndNavigationFinalizer())
        if ctx.update_info is None:
            menu.main_text = translater.translate('✅ Установлена последняя версия FunPay Hub.')
            return menu

        desc = html.escape(ctx.update_info.description)
        if len(desc) > 3000:
            desc = (
                f'{desc[:3000]}...\n\n{translater.translate("Полный список изменений")}'
                ': https://github.com/funpayhub/funpayhub/releases/latest'
            )

        menu.main_text = (
            f'{translater.translate("🔥 <b>Доступно новое обновление</b>!")}\n\n'
            f'<b>{html.escape(ctx.update_info.title)}</b>\n\n'
            f'{desc}'
        )

        menu.main_keyboard = KeyboardBuilder()
        menu.main_keyboard.add_callback_button(
            button_id='download_update',
            text=translater.translate('🔽 Скачать обновление'),
            callback_data=cbs.DownloadUpdate(url=ctx.update_info.url).pack(),
        )

        return menu


class InstallUpdateMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.install_update,
    context_type=InstallUpdateMenuContext,
):
    async def build(self, ctx: InstallUpdateMenuContext, translater: Tr, hub: FunPayHub) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='install_update',
            text=translater.translate('⏬ Установить обновление'),
            callback_data=cbs.InstallUpdate(instance_id=hub.instance_id).pack_compact(),
        )

        return Menu(
            main_text=translater.translate('✅ Обновление скачано.'),
            main_keyboard=kb,
        )
