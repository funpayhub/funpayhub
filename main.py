from __future__ import annotations

import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from funpayhub.lib.translater import Translater
from funpayhub.app.properties.properties import FunPayHubProperties
from funpayhub.app.telegram.handlers.menu import r as menu_router
from funpayhub.app.telegram.middlewares.unhash import UnhashMiddleware
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer
from funpayhub.lib.telegram.menu_constructor.types import PropertiesMenuRenderContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


bot = Bot(
    token=os.environ['FUNPAYHUB_TELEGRAM_TOKEN'], default=DefaultBotProperties(parse_mode='HTML')
)

props = FunPayHubProperties()
props.load()

translater = Translater()
translater.add_translations('funpayhub/locales')

keyboard_hashinater = HashinatorT1000()
renderer = TelegramPropertiesMenuRenderer(translater=translater, hashinator=keyboard_hashinater)

modifier = renderer._overrides['*']
old_footer_builder = modifier.footer_builder

def keyboard_modifier(ctx: PropertiesMenuRenderContext) -> InlineKeyboardMarkup:
    keyboard = old_footer_builder(ctx)

    keyboard.inline_keyboard.insert(
        0,
        [
            InlineKeyboardButton(
                text='Эта блядская кнопка добавлена модификатором',
                callback_data='ushi huinya'
            )
        ]
    )

    return keyboard

modifier.footer_builder = keyboard_modifier
renderer._overrides['*'] = modifier


dp = Dispatcher(
    **{
        'hub_properties': props,
        'tr': translater,
        'menu_renderer': renderer,
        'keyboard_hashinater': keyboard_hashinater,
    }
)

dp.include_router(menu_router)
dp.callback_query.outer_middleware(UnhashMiddleware())


dp.run_polling(bot)
