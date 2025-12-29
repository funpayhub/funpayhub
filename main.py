from __future__ import annotations

import os.path
import sys
import asyncio
import logging
from logging.config import dictConfig

from load_dotenv import load_dotenv
from funpaybotengine import Bot

from funpayhub.app.main import FunPayHub
from funpayhub.app.properties import FunPayHubProperties
from logger_formatter import FileLoggerFormatter, ConsoleLoggerFormatter


load_dotenv()


os.makedirs('logs', exist_ok=True)


LOGGERS = [
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
    'funpayhub.telegram_ui',
    'funpayhub.offers_raiser'
]


dictConfig(
    config={
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'file_formatter': {
                '()': FileLoggerFormatter,
                'fmt': '%(asctime)s %(name)s %(taskName)s %(filename)s[%(lineno)d][%(levelno)s] %(message)s',
                'datefmt': '%d.%m.%Y %H:%M:%S',
            },
            'console_formatter': {
                '()': ConsoleLoggerFormatter,
            }
        },

        'handlers': {
            'console': {
                'formatter': 'console_formatter',
                'level': logging.INFO,
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
                'level': logging.DEBUG
            }
        },
        'loggers': {i: {'level': logging.DEBUG, 'handlers': ['console', 'file']} for i in LOGGERS},
    }
)


async def check_session(bot: Bot):
    session: AioHttpSession = bot.session  # type: ignore
    cs = await session.session()
    async with cs:
        print(await (await cs.get('https://ifconfig.me/ip')).text())


async def main():
    import sys

    print(sys.argv)
    props = FunPayHubProperties()
    await props.load()
    app = FunPayHub(properties=props)
    print(app.instance_id)
    # await check_session(app.funpay.bot)

    for logger_name in LOGGERS:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            print(handler)
            handler.flush()

    result = input()
    if result != 'start':
        sys.exit(0)
    await app.load_plugins()
    await app.start()


if __name__ == '__main__':
    asyncio.run(main())
