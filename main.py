from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from funpayhub.app.telegram.handlers.menu import r as menu_router
from funpayhub.app.telegram.middlewares.unhash import UnhashMiddleware
from funpayhub.app.properties.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
import os


bot = Bot(token=os.environ['FUNPAYHUB_TELEGRAM_TOKEN'], default=DefaultBotProperties(parse_mode='HTML'))

props = FunPayHubProperties()
props.load()

translater = Translater()
translater.add_translations('funpayhub/locales')

keyboard_hashinater = HashinatorT1000()
renderer = TelegramPropertiesMenuRenderer(translater=translater, hashinater=keyboard_hashinater)


dp = Dispatcher(**{
    'hub_properties': props,
    'tr': translater,
    'menu_renderer': renderer,
    'keyboard_hashinater': keyboard_hashinater,
})

dp.include_router(menu_router)
dp.callback_query.outer_middleware(UnhashMiddleware())


dp.run_polling(bot)