from __future__ import annotations

import os
import sys
import subprocess
from copy import deepcopy
from argparse import Namespace, ArgumentParser
from updater import install_dependencies, apply_update
from pathlib import Path
import ctypes
from loggers import launcher as logger
from logger_formatter import FileLoggerFormatter, ConsoleLoggerFormatter, ColorizedLogRecord
import logging
from logging.config import dictConfig

# ---------------------------------------------
# |               Logging setup               |
# ---------------------------------------------
LOGGERS = [logger.name]
os.makedirs('logs', exist_ok=True)

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
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join('logs', 'launcher.log'),
                'encoding': 'utf-8',
                'when': 'D',
                'interval': 1,
                'backupCount': 10,
                'formatter': 'file_formatter',
                'level': logging.DEBUG
            }
        },
        'loggers': {i: {'level': logging.DEBUG, 'handlers': ['console', 'file']} for i in LOGGERS},
    }
)

logging.setLogRecordFactory(ColorizedLogRecord)


# ---------------------------------------------
# |                   Hooks                   |
# ---------------------------------------------
IS_WINDOWS = os.name == 'nt'
RELEASES_PATH = Path(os.environ['RELEASES_PATH']).absolute() if 'RELEASES_PATH' in os.environ else None
APP_PATH = Path(__file__).parent / 'app.py'

logger.info('FunPay Hub launcher is in game!')
logger.info('Working dir: %s', os.getcwd())
logger.info('RELEASES_PATH: %s', RELEASES_PATH)
logger.info('PYTHONPATH: %r', os.environ.get('PYTHONPATH'))


def elevate() -> None:
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        is_admin = False

    if not is_admin:
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit(0)


if IS_WINDOWS:
    logger.info('Running under windows: need elevation.')
    elevate()


parser = ArgumentParser(prog='FunPayHub')
parser.add_argument(
    '-s',
    '--safe',
    action='store_true',
    help='Run FunPayHub in safe mode (without plugins).',
)
original_args = parser.parse_args()
logger.info('Original launch args: %s', original_args)

launch_args = sys.argv[1:]


def namespace_to_argv(ns: Namespace) -> list[str]:
    argv = []
    for key, value in vars(ns).items():
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

    if not RELEASES_PATH:
        logger.error('%s environment variable not set. Unable to apply update.', 'RELEASES_PATH')
        return

    if not (RELEASES_PATH / '.update').exists(follow_symlinks=True):
        logger.error('Update path %s does not exists. Unable to apply update.', RELEASES_PATH)
        return

    # todo: try except
    install_dependencies(RELEASES_PATH / '.update')
    new_version = apply_update(RELEASES_PATH / '.update')
    launcher_path = RELEASES_PATH / 'current' / 'launcher.py'

    logger.info('FunPay Hub update %s applied successfully. Launching new process...', new_version)
    if IS_WINDOWS:
        subprocess.Popen(
            [sys.executable, launcher_path, *launch_args],
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=sys.stdin,
            env=os.environ
        )
    else:
        os.execv(sys.executable, [sys.executable, launcher_path, *launch_args])
    sys.exit(0)



# ---------------------------------------------
# |                 Main loop                 |
# ---------------------------------------------
ACTIONS = {
    0: lambda: sys.exit(0),
    1: update,
    2: safe_restart,
    3: non_safe_restart,
}

while True:
    logger.info('Launching FunPayHub with args: %s', launch_args)

    try:
        result = subprocess.run([sys.executable, APP_PATH, *launch_args],
            env=os.environ.copy(),
        )
    except OSError:
        logger.critical(f'An error occurred while launching FunPayHub.', exc_info=True)
        sys.exit(-1)

    if result.returncode in ACTIONS:
        logger.info('FunPayHub process ended with return code %d.', result.returncode)
        ACTIONS[result.returncode]()
        continue
    else:
        logger.error('FunPayHub process ended with unknoen return code %d.', result.returncode)
        sys.exit(result.returncode)
