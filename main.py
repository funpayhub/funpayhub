from __future__ import annotations

import os
import sys
import logging
from logging.config import dictConfig

from aiogram import Bot, Dispatcher
from load_dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties

from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.app.properties.properties import FunPayHubProperties
from funpayhub.app.telegram.middlewares.unhash import UnpackMiddleware
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
from funpayhub.app.telegram.routers.properties_menu import router as properties_menu_r
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer
from funpayhub.app.telegram.middlewares.add_data_to_workflow_data import AddDataMiddleware


load_dotenv()


dictConfig(
    config={
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'formatter': 'brief',
                'level': logging.DEBUG,
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
            },
        },
        'formatters': {
            'brief': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
        },
        'loggers': {
            'funpaybotengine.session_logger': {
                'level': logging.INFO,
                'handlers': ['console'],
            },
            'eventry.dispatcher': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
            'eventry.router': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
            'aiogram.dispatcher': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
            'aiogram.event': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
            'aiogram.middlewares': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
            'aiogram.webhook': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
            'aiogram.scene': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
        },
    },
)


bot = Bot(
    token=os.environ['FPH_TELEGRAM_TOKEN'],
    default=DefaultBotProperties(parse_mode='HTML'),
)

props = FunPayHubProperties()
props.load()

translater = Translater()
translater.add_translations('funpayhub/locales')
print(translater._catalogs)

keyboard_hashinator = HashinatorT1000()
renderer = TelegramPropertiesMenuRenderer(translater=translater, hashinator=keyboard_hashinator)

registry = UIRegistry(translater=translater, hashinator=keyboard_hashinator)

dp = Dispatcher(
    **{
        'properties': props,
        'translater': translater,
        'menu_renderer': renderer,
        'hashinator': keyboard_hashinator,
        'tg_ui': registry,
    },
)

dp.include_router(properties_menu_r)

middleware = AddDataMiddleware()
for i, o in dp.observers.items():
    if i == 'error':
        continue
    o.outer_middleware(middleware)


dp.callback_query.outer_middleware(UnpackMiddleware())

print('START')
dp.run_polling(bot)
