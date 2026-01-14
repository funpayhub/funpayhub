from __future__ import annotations

import sys
import asyncio
import os.path
from pathlib import Path

import colorama
from load_dotenv import load_dotenv
from funpaybotengine import Bot

from funpayhub.app.main import FunPayHub
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
import logging
from logging.config import dictConfig
from logger_formatter import FileLoggerFormatter, ConsoleLoggerFormatter, ColorizedLogRecord
import os
from utils import set_exception_hook


set_exception_hook()


# ---------------------------------------------
# |               Logging setup               |
# ---------------------------------------------
os.makedirs('logs', exist_ok=True)


LOGGERS = [
    'funpayhub.launcher',
    'funpaybotengine.session',
    'funpaybotengine.runner',
    'eventry.dispatcher',
    'eventry.router',
    'aiogram.dispatcher',
    'aiogram.event',
    'aiogram.middlewares',
    'aiogram.webhook',
    'aiogram.scene',
    'funpayhub.main',
    'funpayhub.telegram',
    'funpayhub.telegram.ui',
    'funpayhub.offers_raiser',
]


dictConfig(
    config={
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'file_formatter': {
                '()': FileLoggerFormatter,
                'fmt': '%(created).3f %(name)s %(taskName)s %(filename)s[%(lineno)d][%(levelno)s] '
                       '%(message)s',
            },
            'console_formatter': {
                '()': ConsoleLoggerFormatter,
            },
        },
        'handlers': {
            'console': {
                'formatter': 'console_formatter',
                'level': logging.DEBUG,
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join('logs', 'fph.log'),
                'encoding': 'utf-8',
                'backupCount': 100,
                'maxBytes': 19 * 1024 * 1024,
                'formatter': 'file_formatter',
                'level': logging.DEBUG,
            },
        },
        'loggers': {i: {'level': logging.DEBUG, 'handlers': ['console', 'file']} for i in LOGGERS},
    },
)

logging.setLogRecordFactory(ColorizedLogRecord)
colorama.just_fix_windows_console()


# ---------------------------------------------
# |                 App start                 |
# ---------------------------------------------
load_dotenv()


async def check_session(bot: Bot):
    session: AioHttpSession = bot.session  # type: ignore
    cs = await session.session()
    async with cs:
        print(await (await cs.get('https://ifconfig.me/ip')).text())


async def main():
    props = FunPayHubProperties()
    await props.load()

    translater = Translater()
    if 'FPH_LOCALES' in os.environ:
        locales_path = Path(os.environ['FPH_LOCALES'])
    else:
        locales_path = Path(__file__).parent / 'locales'
    if locales_path.exists():
        translater.add_translations(locales_path.absolute())

    app = FunPayHub(
        properties=props,
        translater=translater,
    )

    print(app.instance_id)

    # await check_session(app.funpay.bot)
    result = input()
    if result != 'start':
        sys.exit(0)

    await app.load_plugins()
    await app.start()


if __name__ == '__main__':
    logger = logging.getLogger('funpayhub.main')
    logger.info(f'{" Я родился ":-^50}')
    asyncio.run(main())
