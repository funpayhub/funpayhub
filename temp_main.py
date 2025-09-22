from __future__ import annotations

import sys
import asyncio
import logging
from logging.config import dictConfig

from funpayhub.app import FunPayHub
from funpayhub.app.properties import FunPayHubProperties


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
        },
    },
)


async def main():
    props = FunPayHubProperties()
    props.load()

    app = FunPayHub(properties=props)
    await app.start()


if __name__ == '__main__':
    from load_dotenv import load_dotenv

    load_dotenv()
    asyncio.run(main())
