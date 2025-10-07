from __future__ import annotations

import sys
import asyncio
import logging
from logging.config import dictConfig

from load_dotenv import load_dotenv

from funpayhub.app.main import FunPayHub


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
            'funpaybotengine.runner_logger': {
                'level': logging.DEBUG,
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
        },
    },
)


async def main():
    import tracemalloc
    tracemalloc.start()
    try:
        app = FunPayHub()
        await app.load_plugins()
        await app.start()
    except:
        import traceback
        print(traceback.format_exc())
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        for stat in top_stats[:20]:
            print(stat)


if __name__ == '__main__':
    asyncio.run(main())
