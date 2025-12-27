from __future__ import annotations

import sys
import asyncio
import logging
from logging.config import dictConfig

from load_dotenv import load_dotenv
from funpaybotengine import Bot

from funpayhub.app.main import FunPayHub
from funpayhub.app.properties import FunPayHubProperties


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
            'funpaybotengine.session': {
                'level': logging.INFO,
                'handlers': ['console'],
            },
            'funpaybotengine.runner': {
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
            'funpayhub.main': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
            'funpayhub.telegram_ui': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
            'funpayhub.offers_raiser': {
                'level': logging.DEBUG,
                'handlers': ['console'],
            },
        },
    },
)


async def check_session(bot: Bot):
    session: AioHttpSession = bot.session  # type: ignore
    cs = await session.session()
    async with cs:
        print(await (await cs.get('https://ifconfig.me/ip')).text())


async def main():
    props = FunPayHubProperties()
    await props.load()
    app = FunPayHub(properties=props)
    print(app.instance_id)
    await check_session(app.funpay.bot)
    result = input()
    if result != 'start':
        sys.exit(0)
    await app.load_plugins()
    await app.start()


if __name__ == '__main__':
    asyncio.run(main())
