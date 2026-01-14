from __future__ import annotations

import os
import sys
import ctypes
import shutil
import logging
import subprocess
from pathlib import Path
from logging.config import dictConfig

from utils import set_exception_hook
from loggers import bootstrap as logger
from logger_formatter import FileLoggerFormatter, ConsoleLoggerFormatter


set_exception_hook()


# ---------------------------------------------
# |               Logging setup               |
# ---------------------------------------------
LOGGERS = [logger.name]

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
                'colorized': False,
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
                'class': 'logging.FileHandler',
                'filename': os.path.join('logs', 'bootstrap.log'),
                'encoding': 'utf-8',
                'mode': 'w',
                'formatter': 'file_formatter',
                'level': logging.DEBUG,
            },
        },
        'loggers': {i: {'level': logging.DEBUG, 'handlers': ['console', 'file']} for i in LOGGERS},
    },
)


IS_WINDOWS = os.name == 'nt'

RELEASES_PATH = os.path.abspath(os.path.join('releases'))
BOOTSTRAP_PATH = os.path.join(RELEASES_PATH, 'bootstrap')
LAUNCHER_PATH = os.path.join(BOOTSTRAP_PATH, 'launcher.py')
CURRENT_RELEASE_PATH = os.path.join(RELEASES_PATH, 'current')
LOCALES_PATH = os.path.join(CURRENT_RELEASE_PATH, 'locales')


TO_MOVE = {
    'funpayhub',
    'locales',
    'tests',
    'app.py',
    'launcher.py',
    'updater.py',
    'loggers.py',
    'logger_formatter.py',
    'exit_codes.py',
    'requirements.txt',
    'pyproject.toml',
}


def exit(code: int) -> None:
    if IS_WINDOWS and sys.stdin.isatty():
        try:
            input('\nPress Enter to exit...')
        except EOFError:
            pass
    sys.exit(code)


def elevate() -> None:
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        is_admin = False

    if not is_admin:
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, None, 1)
        sys.exit(0)


if IS_WINDOWS:
    elevate()


if os.name == 'nt':
    os.system('title FunPay Hub: 1st launch')


if os.path.exists('releases/current') or os.path.exists('releases/bootstrap'):
    logger.error(
        'FunPay Hub is already bootstrapped. '
        "If this is not the case, remove the 'releases/' directory and try again.",
    )
    exit(1)


def install_dependencies() -> None:
    if not os.path.exists('requirements.txt'):
        logger.warning('requirements.txt not found. Skipping dependencies installation.')

    try:
        result = subprocess.run([sys.executable, '-m', 'ensurepip', '--upgrade'])
        if result.returncode != 0:
            logger.critical('An error occurred while installing pip.')
            exit(result.returncode)
    except:
        logger.critical('An error occurred while installing pip.', exc_info=True)
        exit(1)

    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        if result.returncode != 0:
            logger.critical('An error occurred while updating pip.')
            exit(result.returncode)
    except:
        logger.critical('An error occurred while updating pip.', exc_info=True)
        exit(1)

    requirements_path = Path(__file__).parent / 'requirements.txt'

    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', requirements_path, '-U']
        )
        if result.returncode != 0:
            logger.critical('An error occurred while installing dependencies.')
            exit(result.returncode)
    except:
        logger.critical('An error occurred while installing dependencies.', exc_info=True)
        exit(1)


if '--skip-pip' not in sys.argv:
    install_dependencies()


try:
    os.makedirs(BOOTSTRAP_PATH, exist_ok=True)
except:
    logger.critical('Unable to create bootstrap directory.', exc_info=True)
    exit(2)


try:
    for path in TO_MOVE:
        if not os.path.exists(path):
            logger.critical('Unable to locate %s.', path)
            raise FileNotFoundError(path)
        os.rename(path, os.path.join(BOOTSTRAP_PATH, path))
except:
    logger.critical('An error occurred while moving release files.', exc_info=True)
    if os.path.exists(os.path.join(BOOTSTRAP_PATH)):
        for path in os.listdir(BOOTSTRAP_PATH):
            os.rename(path, '.')
        shutil.rmtree(RELEASES_PATH)
    exit(3)

os.symlink(BOOTSTRAP_PATH, CURRENT_RELEASE_PATH, target_is_directory=True)


logger.info('FunPay Hub successfully installed! Launching...')
env = os.environ.copy()
env['PYTHONPATH'] = os.pathsep.join([CURRENT_RELEASE_PATH, env.get('PYTHONPATH', '')])
env['FPH_LOCALES'] = LOCALES_PATH
env['RELEASES_PATH'] = RELEASES_PATH


if IS_WINDOWS:
    subprocess.Popen(
        [sys.executable, LAUNCHER_PATH],
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=sys.stdin,
        env=env,
    )
else:
    os.execv(sys.executable, [sys.executable, LAUNCHER_PATH])
