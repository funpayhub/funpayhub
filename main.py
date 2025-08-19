from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from funpayhub.telegram.app.handlers.menu import r as menu_router
from funpayhub.app.properties.properties import FunPayHubProperties
import os


bot = Bot(token=os.environ['FUNPAYHUB_TELEGRAM_TOKEN'], default=DefaultBotProperties(parse_mode='HTML'))

props = FunPayHubProperties()
props.load()
dp = Dispatcher(**{'hub_properties': props})
dp.include_router(menu_router)


dp.run_polling(bot)