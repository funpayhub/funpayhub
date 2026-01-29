from __future__ import annotations

from typing import TYPE_CHECKING

import exit_codes
from funpayhub.app.telegram import callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import Menu, Button, MenuContext
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui.types import MenuBuilder, KeyboardBuilder
from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer


if TYPE_CHECKING:
    from funpayhub.app import FunPayHub


class ControlMenuBuilder(MenuBuilder, menu_id=MenuIds.control, context_type=MenuContext):
    async def build(self, ctx: MenuContext, translater: Translater, hub: FunPayHub) -> Menu:
        main_keyboard = KeyboardBuilder()
        main_keyboard.add_rows(
            Button.callback_button(
                button_id='shutdown',
                text=translater.translate('$shutdown'),
                callback_data=cbs.ShutDown(exit_code=exit_codes.SHUTDOWN).pack(),
                row=True,
            ),
            Button.callback_button(
                button_id='restart',
                text=translater.translate('$restart'),
                callback_data=cbs.ShutDown(exit_code=exit_codes.RESTART).pack(),
                row=True,
            ),
            Button.callback_button(
                button_id='restart_switch_safe',
                text=translater.translate('$restart_safe'),
                callback_data=cbs.ShutDown(exit_code=exit_codes.RESTART_SAFE).pack(),
                row=True,
            )
            if not hub.safe_mode
            else Button.callback_button(
                button_id='restart_switch_safe',
                text=translater.translate('$restart_non_safe'),
                callback_data=cbs.ShutDown(exit_code=exit_codes.RESTART_NON_SAFE).pack(),
                row=True,
            ),
            Button.callback_button(
                button_id='update',
                text=translater.translate('$check_updates'),
                callback_data=cbs.CheckForUpdates().pack_compact(),
                row=True,
            ),
        )

        return Menu(
            text=translater.translate('$control_ui_desc'),
            main_keyboard=main_keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )
