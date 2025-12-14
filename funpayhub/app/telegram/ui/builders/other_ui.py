from __future__ import annotations

from funpaybotengine import Bot

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import KeyboardBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, MenuContext
from funpayhub.app.telegram.callbacks import OpenEntryMenu


class AddCommandMenuBuilder(MenuBuilder):
    id = MenuIds.add_command
    context_type = MenuContext

    async def build(self, ctx: MenuContext, translater: Translater) -> Menu:
        return Menu(
            text='$add_command_message',
            footer_keyboard=KeyboardBuilder(
                keyboard=[
                    Button.callback_button(
                        button_id='clear_state',
                        text=translater.translate('$clear_state'),
                        callback_data=cbs.Clear(
                            delete_message=False,
                            open_previous=True,
                            history=ctx.callback_data.history
                            if ctx.callback_data is not None
                            else [],
                        ).pack(),
                        row=True,
                    ),
                ],
            ),
        )


class StartNotificationMenuBuilder(MenuBuilder):
    id = MenuIds.start_notification
    context_type = MenuContext

    async def build(self, ctx: MenuContext, translater: Translater) -> Menu:
        return Menu(
            text=translater.translate('$start_notification_text'),
        )


class FunPaySuccessfulStartNotificationMenuBuilder(MenuBuilder):
    id = MenuIds.successful_funpay_start_notification
    context_type = MenuContext

    async def build(self, ctx: MenuContext, translater: Translater, fp_bot: Bot) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='main',
            text=translater.translate('$main_menu'),
            callback_data=OpenEntryMenu(path=[]).pack(),
        )

        kb.add_callback_button(
            button_id='settings',
            text=translater.translate('$settings'),
            callback_data=OpenEntryMenu(path=[]).pack(),
        )
        text = translater.translate('$funpay_successful_start_notification_text').format(
            username='МихалВадимыч',
            user_id='12345',
            rub_balance='123.45',
            eur_balance='123.45',
            usd_balance='123.45',
        )
        return Menu(
            text=text,
            main_keyboard=kb,
        )
