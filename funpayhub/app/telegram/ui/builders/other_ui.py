from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpaybotengine.exceptions import UnauthorizedError, BotUnauthenticatedError

from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import KeyboardBuilder
from funpayhub.lib.telegram.ui.types import Menu, MenuBuilder, MenuContext
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu, ClearState

from funpayhub.app.telegram.ui.ids import MenuIds

from .context import (
    StateUIContext,
    FunPayStartNotificationMenuContext,
)


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.funpay.main import FunPay


class StartNotificationMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.start_notification,
    context_type=MenuContext,
):
    async def build(self, ctx: MenuContext, translater: Translater, hub: FunPayHub) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='main',
            text=translater.translate('$main_menu'),
            callback_data=OpenMenu(menu_id=MenuIds.main_menu).pack(),
        )

        kb.add_callback_button(
            button_id='settings',
            text=translater.translate('$settings'),
            callback_data=OpenMenu(
                menu_id=MenuIds.props_node,
                context_data={
                    'entry_path': [],
                },
            ).pack(),
        )

        text = translater.translate(
            '🐙 <b><u>FunPay Hub {version} запущен!</u></b>\n\n\n<b>🔄 Подключение к FunPay аккаунту ...</b>\n\n\n<i>⚙️ Вы уже можете пользоваться панелью управления, настраивать бота и т.д.\n\nДля открытия основного меню введите команду /menu\nДля открытия настроек введи команду /settings\n\n📝 После подключения к FunPay аккаунту данное сообщение будет обновлено.</i>'
        ).format(
            version=hub.properties.version.value,
        )

        if hub.safe_mode:
            text += '\n\n' + translater.translate(
                '🛡️ <b><u>FunPayHub запущен в безопасном режиме!</u></b>'
            )
        return Menu(main_text=text)


class FunPayStartNotificationMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.funpay_start_notification,
    context_type=FunPayStartNotificationMenuContext,
):
    async def build(
        self,
        ctx: FunPayStartNotificationMenuContext,
        translater: Translater,
        fp: FunPay,
    ) -> Menu:
        if not ctx.error:
            text = translater.translate(
                '🎉 <b><u>FunPay Hub готов к работе!</u></b>\n\n\n👤 <b><i>Аккаунт: {username} (<a href="https://funpay.com/users/{user_id}/">{user_id}</a>)</i></b>\n\n📊 <b><i>Активные продажи: {active_sells}</i></b>\n📊 <b><i>Активные покупки: {active_purchases}</i></b>\n\n💰 <b><i>Баланс: {rub_balance}₽, {usd_balance}$, {eur_balance}€</i></b>\n💰 <b><i>Сделки: {rub_balance}₽</i></b>\n\n'
            ).format(
                username=fp.bot.username,
                user_id=fp.bot.userid,
                active_sells=(await fp.profile()).header.sales,
                active_purchases=(await fp.profile()).header.purchases,
                rub_balance='123.45',
                eur_balance='123.45',
                usd_balance='123.45',
            )
        elif isinstance(ctx.error, (BotUnauthenticatedError, UnauthorizedError)):
            text = translater.translate(
                '⚠️ <b><u>FunPay Hub запущен, но не удалось авторизоваться!</u></b>\n\n\nℹ️ Проверьте правильность вашего <b>golden_key</b> и попробуйте снова.\n\n🐙 Вы всё ещё можете пользоваться панелью управления через Telegram бота.\n\nДля открытия основного меню введите команду /menu\nДля открытия настроек используйте команду /settings'
            )
        else:
            text = translater.translate(
                '❌ <b><u>Произошла непредвиденная ошибка в FunPay Hub!</u></b>\n\n\nℹ️ Ошибка была зафиксирована, но вы всё ещё можете использовать Telegram бота.\n\nДля открытия основного меню введите команду /menu\nДля открытия настроек используйте команду /settings\n\n📝 Подробности об ошибке можно найти в логах.'
            )

        return Menu(main_text=text)


class MainMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.main_menu,
    context_type=MenuContext,
):
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
            text=translater.translate('⚙️ Настройки'),
            callback_data=OpenMenu(
                menu_id=MenuIds.props_node,
                history=history,
                context_data={'entry_path': []},
            ).pack(),
        )

        kb.add_callback_button(
            button_id='open_control_ui',
            text=translater.translate('🔌 Системное меню'),
            callback_data=OpenMenu(menu_id=MenuIds.control, history=history).pack(),
        )

        kb.add_callback_button(
            button_id='open_formatters_list',
            text=translater.translate('🔖 Форматтеры'),
            callback_data=OpenMenu(menu_id=MenuIds.formatters_list, history=history).pack(),
        )

        kb.add_callback_button(
            button_id='open_goods_sources_list',
            text=translater.translate('🗳 Источники товаров'),
            callback_data=OpenMenu(menu_id=MenuIds.goods_sources_list, history=history).pack(),
        )

        kb.add_callback_button(
            button_id='open_plugins_list',
            text=translater.translate('🧩 Расширения'),
            callback_data=OpenMenu(menu_id=MenuIds.plugins_list, history=history).pack(),
        )

        return Menu(
            main_text=f'🐙 <b><u>FunPay Hub v{hub.properties.version.value}</u></b>',
            main_keyboard=kb,
        )


class StateMenuBuilder(MenuBuilder, menu_id=MenuIds.state_menu, context_type=StateUIContext):
    async def build(self, ctx: StateUIContext, translater: Translater) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='clear_state',
            text=translater.translate('🔘 Отмена'),
            callback_data=ClearState(
                delete_message=ctx.delete_on_clear,
                open_previous=ctx.open_previous_on_clear,
                history=ctx.callback_data.history if ctx.callback_data is not None else [],
            ).pack(),
        )

        return Menu(
            main_text=ctx.text,
            footer_keyboard=kb,
        )


class RequestsMenuBuilder(MenuBuilder, menu_id='fph:request_menu', context_type=MenuContext):
    async def build(self, ctx: MenuContext, hub: FunPayHub) -> Menu:
        counter = hub.funpay.session.counter

        text = (
            f'<b>Запросы к главной странице: {counter.get("") or 0}</b>\n'
            f'<b>Запросы событий: {counter.get("runner/") or 0}</b>\n'
            f'<b>Запросы к профилю: {counter.get(f"users/{hub.funpay.bot.userid}/" or 0)}</b>\n'
        )
        for k, v in hub.funpay.session.counter.items():
            if k in ['runner/', f'users/{hub.funpay.bot.userid}/', '']:
                continue
            text += f'<b>{html.escape(k)}: {v}</b>\n'

        return Menu(main_text=text)
