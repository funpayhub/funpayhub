from __future__ import annotations

from aiogram.types import InlineKeyboardButton

from funpayhub.app.telegram import callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import Menu, Button, MenuContext
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui.types import MenuBuilder
from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer


class ControlMenuBuilder(MenuBuilder):
    id = MenuIds.control
    context_type = MenuContext

    async def build(self, ctx: MenuContext, translater: Translater) -> Menu:
        return Menu(
            text='$control_menu_text',
            main_keyboard=[
                [
                    Button(
                        button_id='shutdown',
                        obj=InlineKeyboardButton(
                            text=translater.translate('$shutdown'),
                            callback_data=cbs.Dummy().pack(),
                        ),
                    ),
                ],
                [
                    Button(
                        button_id='restart',
                        obj=InlineKeyboardButton(
                            text=translater.translate('$restart'),
                            callback_data=cbs.Dummy().pack(),
                        ),
                    ),
                ],
                [
                    Button(
                        button_id='restart_safe',
                        obj=InlineKeyboardButton(
                            text=translater.translate('$restart_safe'),
                            callback_data=cbs.Dummy().pack(),
                        ),
                    ),
                ],
                [
                    Button(
                        button_id='update',
                        obj=InlineKeyboardButton(
                            text=translater.translate('$update'),
                            callback_data=cbs.Dummy().pack(),
                        ),
                    ),
                ],
            ],
            finalizer=StripAndNavigationFinalizer(),
        )
