from __future__ import annotations

import html
import random
from typing import TYPE_CHECKING

from hubplatform.i18n import I18nString
from hubplatform.telegram.ui import (
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
)
from hubplatform.app.components.telegram.menu_ids import MenuIDs as PlatformMenuIDs
from hubplatform.app.components.telegram.ui.callbacks import OpenMenu
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext
from hubplatform.app.components.telegram.expressions.builders import ExpressionsListMenuContext

from ..notifications_ui.ui import NotificationsMenuContext
from ..notifications_ui.menu_ids import NotificationsUIMenuIDs


if TYPE_CHECKING:
    from aiogram import Bot
    from hubplatform.app import HubPlatformApp


APP_NAME = '.hub'

GREETINGS = (
    '👋 Чем займёмся сегодня?',
    '☕️ С чего начнём?',
    '🚀 Куда отправимся?',
    '🛠 Что будем настраивать?',
    '🤔 Что нужно сделать?',
    '✨ Готов к работе, что делаем?',
    '🎯 Какая задача на сегодня?',
    '📈 Поднимем продажи?',
    '🧭 Куда держим курс?',
    '😎 Всё под контролем, что дальше?',
    '🔧 Что подкрутим?',
    '💡 Есть идеи? Выбирайте раздел',
    '🌟 Рад вас видеть! Чем помочь?',
    '🕹 Выбирайте, я слушаю',
    '📋 Что в планах?',
    '🐾 Куда заглянем?',
    '🍀 Пусть сегодня всё продаётся! С чего начнём?',
    '⚡️ Погнали! Что открываем?',
    '🧩 Какой раздел нужен?',
    '🎛 Что будем менять?',
    '🌙 Даже ночью на посту, что нужно?',
    '🦾 Работаю без выходных, что делаем?',
    '📦 Что сегодня в работе?',
    '🔍 Что ищем?',
    '🎉 Отличный день для продаж! Куда идём?',
    '🧘 Спокойно, всё работает, что посмотрим?',
)


def _code_or_dash(value: int | None) -> str:
    return f'<code>{value}</code>' if value is not None else '—'


async def _username(bot: Bot, user_id: int | None) -> str:
    if user_id is None:
        return '—'
    try:
        chat = await bot.get_chat(user_id)
    except Exception:
        return '—'
    return f'@{html.escape(chat.username)}' if chat.username else '—'


registry = UIRegistry()


@registry.add_menu_builder(menu_id='app:main_menu')
async def build_main_menu(
    ctx: MenuBuildContext[MenuContext],
    app: HubPlatformApp,
    telegram_bot: Bot,
) -> MenuBuildingSpec:
    menu = MenuSpec()
    menu.header_text = (
        f'<table compact><tr><td align="center"><b>💠 {APP_NAME} {app.version}</b></td></tr></table>'
    )

    body = ''
    env = ctx.environment
    if env is not None and env.chat_id is not None:
        username = await _username(telegram_bot, env.actor_id)
        body += (
            '<table bordered compact>'
            f'<tr><td>🆔 ID чата</td><td>{_code_or_dash(env.chat_id)}</td></tr>'
            f'<tr><td>🧵 ID топика</td><td>{_code_or_dash(env.thread_id)}</td></tr>'
            f'<tr><td>👤 Имя пользователя</td><td>{username}</td></tr>'
            f'<tr><td>🪪 ID пользователя</td><td>{_code_or_dash(env.actor_id)}</td></tr>'
            '</table>'
            '<hr/>'
        )
    body += f'<p><i>{random.choice(GREETINGS)}</i></p>'
    menu.body_text = body

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:open_properties',
            text=I18nString('⚙️ Настройки'),
            callback_data=OpenMenu(
                menu_id=PlatformMenuIDs.properties.properties_menu,
                context=NodeMenuContext(node_path=[]).dump(),
            ),
        ),
    )

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:open_current_chat_notifications',
            text=I18nString('🔔 Уведомления'),
            callback_data=OpenMenu(
                menu_id=NotificationsUIMenuIDs.current_chat_notifications,
                context=NotificationsMenuContext(category_path=[]).dump(),
            ),
        ),
    )

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:open_goods_sources',
            text=I18nString('📦 Источники товаров'),
            callback_data=OpenMenu(
                menu_id=PlatformMenuIDs.goods_sources.sources_list_menu,
                context=MenuContext().dump(),
            ),
        ),
    )

    menu.main_keyboard.append(
        KeyboardBlockSpec.callback_button(
            block_id='app:open_expressions_list',
            text=I18nString('♾️ Выражения'),
            callback_data=OpenMenu(
                menu_id=PlatformMenuIDs.expressions.expressions_list_menu,
                context=ExpressionsListMenuContext().dump(),
            ),
        ),
    )

    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())
