from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from funpayhub.telegram.app.handlers.menu import r as menu_router
from funpayhub.app.properties.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer
import os


bot = Bot(token=os.environ['FUNPAYHUB_TELEGRAM_TOKEN'], default=DefaultBotProperties(parse_mode='HTML'))

props = FunPayHubProperties()
props.load()

translater = Translater()
translater.add_translations('funpayhub/locales')

renderer = TelegramPropertiesMenuRenderer(translater=translater)

dp = Dispatcher(**{
    'hub_properties': props,
    'tr': translater,
    'menu_renderer': renderer
})

dp.include_router(menu_router)


dp.run_polling(bot)