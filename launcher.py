"""
Лаунчер FunPay Hub.

Запускает `app.py`, который должен находится в той же директории, что и сам лаунчер.

"""

from __future__ import annotations

from funpayhub.utils import set_exception_hook


set_exception_hook()


import os
import sys
import logging
import subprocess
from copy import deepcopy
from pathlib import Path
from argparse import Namespace
from logging.config import dictConfig

import colorama

from funpayhub import exit_codes
from funpayhub.updater import apply_update
from funpayhub.logger_conf import HubLogMessage, FileLoggerFormatter, ConsoleLoggerFormatter

from funpayhub.app.args_parser import args


colorama.just_fix_windows_console()


# ---------------------------------------------
# |               Logging setup               |
# ---------------------------------------------
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
            'console': {
                'formatter': 'console_formatter',
                'level': logging.DEBUG,
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
            },
            'file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join('logs', 'launcher.log'),
                'encoding': 'utf-8',
                'when': 'D',
                'interval': 1,
                'backupCount': 10,
                'formatter': 'file_formatter',
                'level': logging.DEBUG,
            },
        },
        'loggers': {
            None: {'level': logging.DEBUG, 'handlers': ['console', 'file']},
        },
    },
)

logging.setLogRecordFactory(HubLogMessage)
logger = logging.getLogger()

# ---------------------------------------------
# |                   Hooks                   |
# ---------------------------------------------
IS_WINDOWS = os.name == 'nt'
RELEASES_PATH = Path(os.environ.get('RELEASES_PATH', 'releases')).absolute()
APP_PATH = Path(__file__).with_name('app.py').absolute()

logger.info('FunPay Hub launcher is in game!')
logger.info('Working dir: %s', os.getcwd())
logger.info('RELEASES_PATH: %s', RELEASES_PATH)
logger.info('PYTHONPATH: %r', os.environ.get('PYTHONPATH'))

original_args = args
logger.info('Original launch args: %s', original_args)

launch_args = sys.argv[1:]


def namespace_to_argv(ns: Namespace) -> list[str]:
    argv = []
    for key, value in vars(ns).items():
        if value is None:
            continue
        flag = f'--{key.replace("_", "-")}'
        if isinstance(value, bool):
            if value:
                argv.append(flag)
        else:
            argv.extend([flag, str(value)])
    return argv


def safe_restart() -> None:
    logger.info('Restarting FunPayHub in safe mode.')
    global launch_args

    new_args = deepcopy(original_args)
    new_args.safe = True
    launch_args = namespace_to_argv(new_args)


def non_safe_restart() -> None:
    logger.info('Restarting FunPayHub in non-safe mode.')
    global launch_args

    new_args = deepcopy(original_args)
    new_args.safe = False
    launch_args = namespace_to_argv(new_args)


def update() -> None:
    logger.info('Applying FunPayHub update.')

    try:
        new_version = apply_update(RELEASES_PATH / '.update')
        launcher_path = RELEASES_PATH / 'current' / 'launcher.py'
    except Exception:
        logger.critical('An error occurred while updating FunPay Hub.', exc_info=True)
        return

    logger.info('FunPay Hub update %s applied successfully. Launching new process...', new_version)
    if IS_WINDOWS:
        subprocess.Popen(
            [sys.executable, launcher_path, *launch_args],
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=sys.stdin,
            env=os.environ,
        )
    else:
        os.execv(sys.executable, [sys.executable, str(launcher_path), *launch_args])
    sys.exit(0)


def not_a_tty() -> None:
    logger.critical(
        'Cannot start without a TTY: interactive input is required. '
        'Please restart the application from a terminal.',
    )
    sys.exit(exit_codes.NOT_A_TTY)


def telegram_error() -> None:
    logger.critical(
        'An error occurred while initializing the Telegram bot. '
        'The token is most likely invalid. Please update the token and restart the application.',
    )
    sys.exit(exit_codes.TELEGRAM_ERROR)


# ---------------------------------------------
# |                 Main loop                 |
# ---------------------------------------------
ACTIONS = {
    exit_codes.SHUTDOWN: lambda: sys.exit(0),
    exit_codes.UPDATE: update,
    exit_codes.RESTART: lambda: True,
    exit_codes.RESTART_SAFE: safe_restart,
    exit_codes.RESTART_NON_SAFE: non_safe_restart,
    exit_codes.NOT_A_TTY: not_a_tty,
    exit_codes.TELEGRAM_ERROR: telegram_error,
}

while True:
    logger.info('Launching FunPayHub with args: %s', launch_args)

    try:
        result = subprocess.run(
            [sys.executable, APP_PATH, *launch_args],
            env=os.environ.copy(),
        )
    except OSError:
        logger.critical('An error occurred while launching FunPayHub.', exc_info=True)
        sys.exit(-1)

    if result.returncode in ACTIONS:
        logger.info('FunPayHub process ended with return code %d.', result.returncode)
        ACTIONS[result.returncode]()
        continue
    else:
        logger.error('FunPayHub process ended with unknown return code %d.', result.returncode)
        raise Exception
