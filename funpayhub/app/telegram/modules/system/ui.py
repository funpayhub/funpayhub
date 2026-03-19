from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub import exit_codes

from funpayhub.lib.telegram.ui import Menu, Button, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from funpayhub.app.telegram.ui.ids import MenuIds

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater

    from funpayhub.app.main import FunPayHub


class ControlMenuBuilder(MenuBuilder, menu_id=MenuIds.control, context_type=MenuContext):
    async def build(self, ctx: MenuContext, translater: Translater, hub: FunPayHub) -> Menu:
        from funpayhub.app.telegram.modules.updates.callbacks import CheckForUpdates

        main_keyboard = KeyboardBuilder()
        main_keyboard.add_rows(
            Button.callback_button(
                button_id='shutdown',
                text=translater.translate('⏻ Выключить FPH'),
                callback_data=cbs.ShutDown(exit_code=exit_codes.SHUTDOWN).pack(),
                row=True,
            ),
            Button.callback_button(
                button_id='restart',
                text=translater.translate('🔄 Перезапустить FPH'),
                callback_data=cbs.ShutDown(exit_code=exit_codes.RESTART).pack(),
                row=True,
            ),
            Button.callback_button(
                button_id='restart_switch_safe',
                text=translater.translate('🛡️ Безопасный режим'),
                callback_data=cbs.ShutDown(exit_code=exit_codes.RESTART_SAFE).pack(),
                row=True,
            )
            if not hub.safe_mode
            else Button.callback_button(
                button_id='restart_switch_safe',
                text=translater.translate('🚀 Стандартный режим'),
                callback_data=cbs.ShutDown(exit_code=exit_codes.RESTART_NON_SAFE).pack(),
                row=True,
            ),
            Button.callback_button(
                button_id='update',
                text=translater.translate('🔍 Проверить наличие обновлений'),
                callback_data=CheckForUpdates().pack_compact(),
                row=True,
            ),
        )

        return Menu(
            main_text=translater.translate('🔌 <b>Системное меню</b>'),
            main_keyboard=main_keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )
