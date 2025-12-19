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
        self,
        ctx: MenuContext,
        properties: FunPayHubProperties,
        translater: Translater,
    ) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='no_proxy',
            text='$skip_proxy_setup',
            callback_data=cbs.SetupProxy(
                action=cbs.ProxyAction.no_proxy,
                history=ctx.callback_data.as_history(),
            ).pack(),
        )

        if ctx.data.get('proxy_env'):
            kb.add_callback_button(
                button_id='proxy_from_env',
                text='$use_proxy_from_env',
                callback_data=cbs.SetupProxy(
                    action=cbs.ProxyAction.from_env,
                    history=ctx.callback_data.as_history(),
                ).pack(),
            )

        if ctx.data.get('proxy_props'):
            kb.add_callback_button(
                button_id='proxy_from_props',
                text='$use_proxy_from_props',
                callback_data=cbs.SetupProxy(
                    action=cbs.ProxyAction.from_properties,
                    history=ctx.callback_data.as_history(),
                ).pack(),
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
        self,
        ctx: MenuContext,
        properties: FunPayHubProperties,
        translater: Translater,
    ) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='default_user_agent',
            text='$default_user_agent',
            callback_data='default_user_agent',
        )

        if ctx.data.get('user_agent_env'):
            kb.add_callback_button(
                button_id='user_agent_from_env',
                text='$use_user_agent_from_env',
                callback_data=cbs.SetupProxy(
                    action=cbs.ProxyAction.from_env,
                    history=ctx.callback_data.as_history(),
                ).pack(),
            )

        if ctx.data.get('user_agent_props'):
            kb.add_callback_button(
                button_id='user_agent_from_props',
                text='$use_user_agent_from_props',
                callback_data=cbs.SetupProxy(
                    action=cbs.ProxyAction.from_properties,
                    history=ctx.callback_data.as_history(),
                ).pack(),
            )

        return Menu(
            text=translater.translate('$setup_enter_user_agent'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )


class EnterGoldenKeyMenu(MenuBuilder):
    id = 'fph:setup_enter_golden_key'
    context_type = MenuContext

    async def build(self, ctx: MenuContext, translater: Translater) -> Menu:
        kb = KeyboardBuilder()

        kb.add_callback_button(
            button_id='no_golden_key',
            text='$skip_golden_key_setup',
            callback_data=cbs.SetupGoldenKey(
                action=cbs.GoldenKeyAction.no_golden_key,
                history=ctx.callback_data.as_history(),
            ).pack(),
        )

        if ctx.data.get('golden_key_env'):
            kb.add_callback_button(
                button_id='golden_key_from_env',
                text='$use_golden_key_from_env',
                callback_data=cbs.SetupGoldenKey(
                    action=cbs.GoldenKeyAction.from_env,
                    history=ctx.callback_data.as_history(),
                ).pack(),
            )

        if ctx.data.get('golden_key_props'):
            kb.add_callback_button(
                button_id='golden_key_from_props',
                text='$use_golden_key_from_props',
                callback_data=cbs.SetupGoldenKey(
                    action=cbs.GoldenKeyAction.from_properties,
                    history=ctx.callback_data.as_history(),
                ).pack(),
            )

        return Menu(
            text=translater.translate('$setup_enter_golden_key'),
            finalizer=StripAndNavigationFinalizer(),
        )
