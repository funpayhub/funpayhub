from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from funpayhub.telegram.app.handlers.menu import r as menu_router
from funpayhub.app.properties.properties import FunPayHubProperties
from funpayhub.translater import Translater
import os


bot = Bot(token=os.environ['FUNPAYHUB_TELEGRAM_TOKEN'], default=DefaultBotProperties(parse_mode='HTML'))

props = FunPayHubProperties()
props.load()
translater = Translater()
translater.add_translations('funpayhub/locales')
print(translater.translate("$props.telegram:name", "ru"))
dp = Dispatcher(**{'hub_properties': props, 'tr': translater})
dp.include_router(menu_router)


dp.run_polling(bot)