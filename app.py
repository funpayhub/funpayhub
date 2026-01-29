from __future__ import annotations

from utils import set_exception_hook


set_exception_hook()


import os
import sys
import asyncio
import logging
import os.path
from typing import Any
from pathlib import Path
from argparse import ArgumentParser
from logging.config import dictConfig

import colorama
from load_dotenv import load_dotenv

from logger_conf import (
    HubLogMessage,
    FileLoggerFormatter,
    ConsoleLoggerFormatter,
)
from funpayhub.app.main import FunPayHub
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater


# move
parser = ArgumentParser(prog='FunPayHub')
parser.add_argument(
    '-s',
    '--safe',
    action='store_true',
    help='Run FunPayHub in safe mode (without plugins).',
)
parser.add_argument(
    '-d',
    '--debug',
    action='store_true',
    help='Run FunPayHub in debug mode.',
)
original_args = parser.parse_args()


# ---------------------------------------------
# |               Logging setup               |
# ---------------------------------------------
translater = Translater()
os.makedirs('logs', exist_ok=True)


LOGGERS = [
    'funpaybotengine.session',
    'funpaybotengine.runner',
    'eventry.dispatcher',
    'eventry.router',
    'aiogram',
    'funpayhub',
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
            'console_debug': {
                'formatter': 'console_formatter',
                'level': logging.DEBUG,
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
            },
            'console_info': {
                'formatter': 'console_formatter',
                'level': logging.INFO,
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
            },
            'console_warning': {
                'formatter': 'console_formatter',
                'level': logging.WARNING,
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
        'loggers': {
            'aiogram': {
                'level': logging.INFO if not original_args.debug else logging.DEBUG,
                'handlers': ['console_warning', 'file'],
            },
            **{
                i: {
                    'level': logging.INFO if not original_args.debug else logging.DEBUG,
                    'handlers': ['console_debug', 'file'],
                }
                for i in LOGGERS
                if i not in ['aiogram']
            },
        },
    },
)


def log_factory(*args: Any, **kwargs: Any) -> HubLogMessage:
    return HubLogMessage(*args, translater=translater, **kwargs)


logging.setLogRecordFactory(log_factory)
colorama.just_fix_windows_console()


# ---------------------------------------------
# |                 App start                 |
# ---------------------------------------------
load_dotenv()


async def main() -> None:
    props = FunPayHubProperties()
    await props.load()
    translater.current_language = props.general.language.real_value

    if 'FPH_LOCALES' in os.environ:
        locales_path = Path(os.environ['FPH_LOCALES'])
    else:
        locales_path = Path(__file__).parent / 'locales'
    if locales_path.exists():
        translater.add_translations(locales_path.absolute())

    app = FunPayHub(
        properties=props,
        translater=translater,
        safe_mode=original_args.safe,
    )

    await app.setup()
    exit_code = await app.start()
    sys.exit(exit_code)


if __name__ == '__main__':
    logger = logging.getLogger('funpayhub.main')
    logger.info(f'{" Я родился ":-^50}')
    asyncio.run(main())
