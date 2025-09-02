from __future__ import annotations

import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from funpayhub.lib.translater import Translater
from funpayhub.app.properties.properties import FunPayHubProperties
from funpayhub.app.telegram.routers.properties_menu import router as properties_menu_r
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

dp = Dispatcher(
    **{
        'hub_properties': props,
        'translater': translater,
        'menu_renderer': renderer,
        'keyboard_hashinater': keyboard_hashinater,
    }
)

print(properties_menu_r.name)
print(properties_menu_r.callback_query.handlers)
dp.include_router(properties_menu_r)
dp.callback_query.outer_middleware(UnhashMiddleware())


dp.run_polling(bot)
