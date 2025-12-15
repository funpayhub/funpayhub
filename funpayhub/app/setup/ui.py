from __future__ import annotations

from funpayhub.lib import Translater
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.telegram.ui import Menu, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.app.telegram.callbacks import OpenMenu
from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer

from . import callbacks as cbs


class SelectLanguageMenu(MenuBuilder):
    id = 'fph:setup_select_language'
    context_type = MenuContext

    async def build(self, ctx: MenuContext, properties: FunPayHubProperties) -> Menu:
        kb = KeyboardBuilder()
        for i in properties.general.language.choices.values():
            kb.add_callback_button(
                button_id=f'set_setup_language:{i.value}',
                text=i.name,
                callback_data=cbs.SelectSetupLanguage(
                    lang=i.value,
                    history=[OpenMenu(menu_id='fph:setup_select_language').pack(hash=False)],
                ).pack(),
            )

        return Menu(
            text='👋🙂❗\n\n🗣️❓ 🌍💬 ❓\n\n👇',
            footer_keyboard=kb,
        )


class EnterProxyMenu(MenuBuilder):
    id = 'fph:setup_enter_proxy'
    context_type = MenuContext

    async def build(
        self, ctx: MenuContext, properties: FunPayHubProperties, translater: Translater
    ) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='no_proxy',
            text='$skip_proxy_setup',
            callback_data='skip_proxy_setup',
        )

        return Menu(
            text=translater.translate('$setup_enter_proxy_message'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )


class EnterUserAgentMenu(MenuBuilder):
    id = 'fph:setup_enter_user_agent'
    context_type = MenuContext

    async def build(
        self, ctx: MenuContext, properties: FunPayHubProperties, translater: Translater
    ) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='default_user_agent',
            text='$default_user_agent',
            callback_data='default_user_agent',
        )

        return Menu(
            text=translater.translate('$setup_enter_user_agent'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )
