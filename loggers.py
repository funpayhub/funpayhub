from __future__ import annotations

from logging import getLogger
import colorama
import logging
from logging.config import dictConfig
from logger_formatter import FileLoggerFormatter, ConsoleLoggerFormatter, ColorizedLogRecord
import os
import sys


colorama.just_fix_windows_console()


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
    'funpayhub.offers_raiser'
]


dictConfig(
    config={
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'file_formatter': {
                '()': FileLoggerFormatter,
                'fmt': '%(created).3f %(name)s %(taskName)s %(filename)s[%(lineno)d][%(levelno)s] %(message)s',
            },
            'console_formatter': {
                '()': ConsoleLoggerFormatter,
            }
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
                'level': logging.DEBUG
            }
        },
        'loggers': {i: {'level': logging.DEBUG, 'handlers': ['console', 'file']} for i in LOGGERS},
    }
)

logging.setLogRecordFactory(ColorizedLogRecord)


launcher = getLogger('funpayhub.launcher')
updater = getLogger('funpayhub.updater')
main = getLogger('funpayhub.main')
telegram = getLogger('funpayhub.telegram')
telegram_ui = getLogger('funpayhub.telegram.ui')
callbacks = getLogger('funpayhub.callbacks')
offers_raiser = getLogger('funpayhub.offers_raiser')
