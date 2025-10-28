from aiogram.types import InlineKeyboardButton

from funpayhub.app.telegram.ui.premade import default_finalizer_factory
from funpayhub.lib.telegram.ui import Menu, Button, MenuContext
from funpayhub.lib.telegram import callbacks as cbs
from funpayhub.lib.translater import Translater


async def control_ui_menu_builder(ctx: MenuContext, translater: Translater) -> Menu:
    return Menu(
        text='$control_menu_text',
        main_keyboard=[
            [Button(
                button_id='shutdown',
                obj=InlineKeyboardButton(
                    text=translater.translate('$shutdown'),
                    callback_data=cbs.Dummy().pack()
                )
            )],
            [Button(
                button_id='restart',
                obj=InlineKeyboardButton(
                    text=translater.translate('$restart'),
                    callback_data=cbs.Dummy().pack()
                )
            )],
            [Button(
                button_id='restart_safe',
                obj=InlineKeyboardButton(
                    text=translater.translate('$restart_safe'),
                    callback_data=cbs.Dummy().pack()
                )
            )],
            [Button(
                button_id='update',
                obj=InlineKeyboardButton(
                    text=translater.translate('$update'),
                    callback_data=cbs.Dummy().pack()
                )
            )],
        ],
        finalizer=default_finalizer_factory()
    )