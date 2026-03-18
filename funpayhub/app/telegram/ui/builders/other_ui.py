from __future__ import annotations

import html
from typing import TYPE_CHECKING

from funpaybotengine.exceptions import UnauthorizedError, BotUnauthenticatedError

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.translater import Translater, translater
from funpayhub.lib.telegram.ui import Button, KeyboardBuilder
from funpayhub.lib.telegram.ui.types import Menu, MenuBuilder, MenuContext, MenuContextOld
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu, ClearState
from funpayhub.lib.base_app.telegram.app.ui.ui_finalizers import StripAndNavigationFinalizer

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.callbacks import SendMessage

from .context import (
    StateUIContext,
    NewReviewNotificationMenuContext,
    FunPayStartNotificationMenuContext,
)


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.funpay.main import FunPay


ru = translater.translate


class StartNotificationMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.start_notification,
    context_type=MenuContextOld,
):
    async def build(self, ctx: MenuContextOld, translater: Translater, hub: FunPayHub) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='main',
            text=translater.translate('🏠 Главное меню'),
            callback_data=OpenMenu(menu_id=MenuIds.main_menu).pack(),
        )

        kb.add_callback_button(
            button_id='settings',
            text=translater.translate('⚙️ Меню настроек'),
            callback_data=OpenMenu(
                menu_id=MenuIds.props_node,
                context_data={
                    'entry_path': [],
                },
            ).pack(),
        )

        text = translater.translate(
            '🐙 <b><u>FunPay Hub {version} запущен!</u></b>\n\n\n'
            '<b>🔄 Подключение к FunPay аккаунту ...</b>\n\n\n'
            '<i>⚙️ Вы уже можете пользоваться панелью управления, настраивать бота и т.д.\n\n'
            'Для открытия основного меню введите команду /menu\n'
            'Для открытия настроек введи команду /settings\n\n'
            '📝 После подключения к FunPay аккаунту данное сообщение будет обновлено.</i>',
        ).format(
            version=hub.properties.version.value,
        )

        if hub.safe_mode:
            text += '\n\n' + translater.translate(
                '🛡️ <b><u>FunPayHub запущен в безопасном режиме!</u></b>',
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
            page = await fp.bot.get_transactions_page()
            text = translater.translate(
                '🎉 <b><u>FunPay Hub готов к работе!</u></b>\n\n\n'
                '👤 <b><i>Аккаунт: {username} '
                '(<a href="https://funpay.com/users/{user_id}/">{user_id}</a>)</i></b>\n\n'
                '📊 <b><i>Активные продажи: {active_sells}</i></b>'
                '\n📊 <b><i>Активные покупки: {active_purchases}</i></b>\n\n'
                '💰 <b><i>Баланс: {rub_balance}₽, {usd_balance}$, {eur_balance}€</i></b>\n'
                '💰 <b><i>Сделки: {deals_balance}₽</i></b>\n\n'
                'Для открытия основного меню введите команду /menu\n'
                'Для открытия настроек используйте команду /settings',
            ).format(
                username=fp.bot.username,
                user_id=fp.bot.userid,
                active_sells=page.header.sales,
                active_purchases=page.header.purchases,
                rub_balance=page.rub_balance.value if page.rub_balance else 0,
                usd_balance=page.usd_balance.value if page.usd_balance else 0,
                eur_balance=page.eur_balance.value if page.eur_balance else 0,
                deals_balance=page.deals_balance.value if page.deals_balance else 0,
            )
        elif isinstance(ctx.error, (BotUnauthenticatedError, UnauthorizedError)):
            text = translater.translate(
                '⚠️ <b><u>FunPay Hub запущен, но не удалось авторизоваться!</u></b>\n\n\n'
                'ℹ️ Проверьте правильность вашего <b>golden_key</b> и попробуйте снова.\n\n'
                '🐙 Вы всё ещё можете пользоваться панелью управления через Telegram бота.\n\n'
                'Для открытия основного меню введите команду /menu\n'
                'Для открытия настроек используйте команду /settings',
            )
        else:
            text = translater.translate(
                '❌ <b><u>Произошла непредвиденная ошибка в FunPay Hub!</u></b>\n\n\n'
                'ℹ️ Ошибка была зафиксирована, но вы всё ещё можете использовать Telegram бота.\n\n'
                'Для открытия основного меню введите команду /menu\n'
                'Для открытия настроек используйте команду /settings\n\n'
                '📝 Подробности об ошибке можно найти в логах.',
            )

        return Menu(main_text=text)


class MainMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.main_menu,
    context_type=MenuContext,
):
    async def build(self, ctx: MenuContext, hub: FunPayHub) -> Menu:
        kb = KeyboardBuilder()
        kb.add_callback_button(
            button_id='settings',
            text=ru('⚙️ Настройки'),
            callback_data=OpenMenu(
                menu_id=MenuIds.props_node,
                ui_history=ctx.as_ui_history(),
                context_data={'entry_path': []},
            ).pack(),
        )

        kb.add_callback_button(
            button_id='open_control_ui',
            text=ru('🔌 Системное меню'),
            callback_data=OpenMenu(menu_id=MenuIds.control, ui_history=ctx.as_ui_history()).pack(),
        )

        kb.add_callback_button(
            button_id='open_formatters_list',
            text=ru('🔖 Форматтеры'),
            callback_data=OpenMenu(
                menu_id=MenuIds.formatters_list,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        kb.add_callback_button(
            button_id='open_goods_sources_list',
            text=ru('🗳 Источники товаров'),
            callback_data=OpenMenu(
                menu_id=MenuIds.goods_sources_list,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        kb.add_callback_button(
            button_id='open_plugins_list',
            text=ru('🧩 Расширения'),
            callback_data=OpenMenu(
                menu_id=MenuIds.plugins_list,
                ui_history=ctx.as_ui_history(),
            ).pack(),
        )

        return Menu(
            main_text=f'🐙 <b><u>FunPay Hub v{hub.properties.version.value}</u></b>',
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
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
                ui_history=ctx.ui_history,
            ).pack(),
        )

        return Menu(
            main_text=ctx.text,
            footer_keyboard=kb,
        )


class RequestsMenuBuilder(MenuBuilder, menu_id='fph:request_menu', context_type=MenuContextOld):
    async def build(self, ctx: MenuContextOld, hub: FunPayHub) -> Menu:
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


class NewReviewNotificationMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.review_notification,
    context_type=NewReviewNotificationMenuContext,
):
    async def build(self, ctx: NewReviewNotificationMenuContext, translater: Translater) -> Menu:
        order_page = await ctx.review_event.get_order_page()
        menu = Menu(finalizer=StripAndNavigationFinalizer())

        menu.header_text = translater.translate(
            '<b>🌟 Вам оставили новый отзыв за заказ <a href="https://funpay.com/orders/{orderid}/">{orderid}</a>!</b>',
        ).format(orderid=order_page.order_id)

        menu.main_text = translater.translate(
            '📦 <b>Лот: {order_name}</b>\n'
            '👤 <b>Пользователь: <a href="https://funpay.com/users/{userid}/">{username}</a></b>\n'
            '⭐️ <b>Оценка: {rating} / 5</b>\n\n'
            '💬 <b>Текст отзыва:</b>\n'
            '<blockquote>{review_text}</blockquote>',
        ).format(
            order_name=order_page.short_description,
            userid=str(order_page.chat.interlocutor.id),
            username=order_page.chat.interlocutor.username,
            rating=str(order_page.review.rating),
            review_text=html.escape(order_page.review.text),
        )

        if ctx.review_event.data.get('review_reply_error'):
            err = ctx.review_event.data['review_reply_error']
            if isinstance(err, TranslatableException):
                err_text = err.format_args(translater.translate(err.message))
            else:
                err_text = translater.translate('Подробности в логах.')

            menu.main_text += (
                '\n\n'
                + translater.translate(
                    '❌ Произоша ошибка при ответе на отзыв.',
                )
                + '\n'
                + html.escape(err_text)
            )
        elif ctx.review_event.data.get('review_reply_text'):
            text = html.escape(ctx.review_event.data['review_reply_text'])
            menu.main_text += (
                '\n\n'
                + translater.translate('💬 <b>Текст ответа:</b>')
                + f'\n<blockquote>{text}</blockquote>'
            )

        if ctx.review_event.data.get('chat_reply_error'):
            err = ctx.review_event.data['chat_reply_error']
            if isinstance(err, TranslatableException):
                err_text = err.format_args(translater.translate(err.message))
            else:
                err_text = translater.translate('Подробности в логах.')

            menu.main_text += (
                '\n\n'
                + translater.translate(
                    '❌ Произоша ошибка при ответе в чате на отзыв.',
                )
                + '\n'
                + html.escape(err_text)
            )
        elif ctx.review_event.data.get('chat_reply_text'):
            text = html.escape(ctx.review_event.data['chat_reply_text'])
            menu.main_text += (
                '\n\n'
                + translater.translate('💬 <b>Текст ответа в чате:</b>')
                + f'\n<blockquote>{text}</blockquote>'
            )

        menu.header_keyboard.add_row(
            Button.callback_button(
                button_id='answer_in_chat',
                text=translater.translate('💬 Отв. в чат'),
                callback_data=SendMessage(
                    to=order_page.chat.id,
                    name=order_page.chat.interlocutor.username,
                ).pack_compact(),
            ),
            Button.url_button(
                button_id='open_chat',
                text=translater.translate('💬 Чат'),
                url=f'https://funpay.com/chat/?node={order_page.chat.id}',
            ),
            Button.url_button(
                button_id='open_order',
                text=translater.translate('🏷️ Заказ'),
                url=f'https://funpay.com/orders/{order_page.order_id}',
            ),
        )
        return menu
