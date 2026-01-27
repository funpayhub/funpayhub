from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any

from funpaybotengine.exceptions import UnauthorizedError, BotUnauthenticatedError

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import KeyboardBuilder
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, MenuContext
from funpayhub.app.telegram.callbacks import OpenEntryMenu

from .context import (
    UpdateMenuContext,
    InstallUpdateMenuContext,
    FunPayStartNotificationMenuContext, StateUIContext,
)
from ..premade import StripAndNavigationFinalizer


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.funpay.main import FunPay


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

    async def build(self, ctx: MenuContext, translater: Translater, hub: FunPayHub) -> Menu:
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

        text = translater.translate('$start_notification_text').format(
            version=hub.properties.version.value,
        )

        if hub.safe_mode:
            text += '\n\n' + translater.translate('$safe_mode_enabled')
        return Menu(text=text)


class FunPayStartNotificationMenuBuilder(MenuBuilder):
    id = MenuIds.funpay_start_notification
    context_type = FunPayStartNotificationMenuContext

    async def build(
        self,
        ctx: FunPayStartNotificationMenuContext,
        translater: Translater,
        fp: FunPay,
    ) -> Menu:
        if not ctx.error:
            text = translater.translate('$funpay_successful_start_notification_text').format(
                username=fp.bot.username,
                user_id=fp.bot.userid,
                active_sells=(await fp.profile()).header.sales,
                active_purchases=(await fp.profile()).header.purchases,
                rub_balance='123.45',
                eur_balance='123.45',
                usd_balance='123.45',
            )
        elif isinstance(ctx.error, (BotUnauthenticatedError, UnauthorizedError)):
            text = translater.translate('$funpay_unauthenticated_start_notification_text')
        else:
            text = translater.translate('$funpay_unexpected_error_notification_text')

        return Menu(text=text)


class UpdateMenuBuilder(MenuBuilder):
    id = MenuIds.update
    context_type = UpdateMenuContext

    async def build(self, ctx: UpdateMenuContext, translater: Translater) -> Menu:
        menu = Menu(finalizer=StripAndNavigationFinalizer())
        if ctx.update_info is None:
            menu.text = translater.translate('$no_updates_available')
            return menu

        desc = html.escape(ctx.update_info.description)
        if len(desc) > 3000:
            desc = (
                desc[:3000]
                + '...'
                + '\n\n'
                + translater.translate('$full_changelog')
                + ': https://github.com/funpayhub/funpayhub/releases/latest'
            )

        menu.text = f"""{translater.translate('$new_update_available')}

<b>{html.escape(ctx.update_info.title)}</b>

{desc}"""

        menu.main_keyboard = KeyboardBuilder()
        menu.main_keyboard.add_callback_button(
            button_id='download_update',
            text=translater.translate('$download_update'),
            callback_data=cbs.DownloadUpdate(url=ctx.update_info.url).pack(),
        )

        return menu


class InstallUpdateMenuBuilder(MenuBuilder):
    id = MenuIds.install_update
    context_type = InstallUpdateMenuContext

    async def build(
        self,
        ctx: InstallUpdateMenuContext,
        translater: Translater,
        hub: FunPayHub,
    ) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='install_update',
            text=translater.translate('$install_update'),
            callback_data=cbs.InstallUpdate(instance_id=hub.instance_id).pack_compact(),
        )

        return Menu(
            text=translater.translate('$install_update_text'),
            main_keyboard=kb,
        )


class MainMenuBuilder(MenuBuilder):
    id = MenuIds.main_menu
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        translater: Translater,
        hub: FunPayHub,
    ):
        history = ctx.callback_data.as_history() if ctx.callback_data is not None else []

        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='settings',
            text=translater.translate('$props:name'),
            callback_data=cbs.OpenEntryMenu(path=[], history=history).pack(),
        )

        kb.add_callback_button(
            button_id='open_control_ui',
            text=translater.translate('$control_ui'),
            callback_data=cbs.OpenMenu(menu_id=MenuIds.control, history=history).pack(),
        )

        kb.add_callback_button(
            button_id='open_formatters_list',
            text=translater.translate('$open_formatters_list'),
            callback_data=cbs.OpenMenu(menu_id=MenuIds.formatters_list, history=history).pack(),
        )

        kb.add_callback_button(
            button_id='open_goods_sources_list',
            text=translater.translate('$goods_sources_list'),
            callback_data=cbs.OpenMenu(menu_id=MenuIds.goods_sources_list, history=history).pack(),
        )

        kb.add_callback_button(
            button_id='open_plugins_list',
            text=translater.translate('$plugins_list'),
            callback_data=cbs.OpenMenu(menu_id=MenuIds.plugins_list, history=history).pack(),
        )

        return Menu(
            text=f'🐙 <b><u>FunPay Hub v{hub.properties.version.value}</u></b>',
            main_keyboard=kb,
        )


class StateMenuBuilder(MenuBuilder):
    id = MenuIds.state_menu
    context_type = StateUIContext
    
    async def build(self, ctx: StateUIContext, translater: Translater) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='clear_state',
            text=translater.translate('$clear_state'),
            callback_data=cbs.Clear(
                delete_message=ctx.delete_on_clear,
                open_previous=ctx.open_previous_on_clear,
                history=ctx.callback_data.history if ctx.callback_data is not None else [],
            ).pack()
        )
        
        return Menu(
            text=ctx.text,
            footer_keyboard=kb
        )
