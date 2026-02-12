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
from logging.config import dictConfig

import colorama

from logger_conf import (
    HubLogMessage,
    FileLoggerFormatter,
    ConsoleLoggerFormatter,
)

from funpayhub.lib.translater import Translater

from funpayhub.app.main import FunPayHub
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.app.args_parser import args


# ---------------------------------------------
# |               Logging setup               |
# ---------------------------------------------
translater = Translater()
os.makedirs('logs', exist_ok=True)


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
        'loggers': {
            None: {
                'level': logging.DEBUG if args.debug else logging.INFO,
                'handlers': ['console', 'file'],
            },
            'aiogram': {
                'level': logging.DEBUG if args.debug else logging.WARNING,
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
        safe_mode=args.safe,
    )

    if app.telegram.bot.token and not props.telegram.general.token.value:
        await props.telegram.general.token.set_value(app.telegram.bot.token)

    await app.setup()
    exit_code = await app.start()
    sys.exit(exit_code)


if __name__ == '__main__':
    logger = logging.getLogger('funpayhub.main')
    logger.info(f'{" Я родился ":-^50}')
    asyncio.run(main())
