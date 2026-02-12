from __future__ import annotations

import os
import sys


IS_WINDOWS = os.name == 'nt'


def exception_hook(exc_type, exc, tb) -> None:
    sys.__excepthook__(exc_type, exc, tb)
    if IS_WINDOWS:
        try:
            input('\nPress Enter to exit...')
        except EOFError:
            pass


sys.excepthook = exception_hook


import uuid
import ctypes
import shutil
import logging
import tomllib
import argparse
import subprocess
from pathlib import Path
from logging.config import dictConfig


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
                'fmt': '%(created).3f %(name)s %(taskName)s %(filename)s[%(lineno)d][%(levelno)s] '
                '%(message)s',
            },
            'console_formatter': {
                'fmt': '[%(asctime)s] [%(levelname)s:9] %(message)s',
                'datefmt': '%H:%M:%S',
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
        'loggers': {None: {'level': logging.DEBUG, 'handlers': ['console', 'file']}},
    },
)

logger = logging.getLogger()

parser = argparse.ArgumentParser(description='FunPay Hub Bootstrap')

parser.add_argument(
    '--no-deps',
    action='store_true',
    help='Skip dependencies installation.',
)

parser.add_argument(
    '-t',
    '--token',
    type=str,
    default=None,
    help='Telegram bot token to pass to launcher.',
)

args = parser.parse_args()


# ---------------------------------------------
# |                  Consts                   |
# ---------------------------------------------
UNIQUE = uuid.uuid4().hex
RELEASES_PATH = Path('releases').absolute()
TEMP_BOOTSTRAP_PATH = RELEASES_PATH / UNIQUE
BOOTSTRAP_PATH = RELEASES_PATH / 'bootstrap'
LAUNCHER_PATH = BOOTSTRAP_PATH / 'launcher.py'
CURRENT_RELEASE_PATH = RELEASES_PATH / 'current'
LOCALES_PATH = CURRENT_RELEASE_PATH / 'locales'


TO_MOVE = {
    'funpayhub': True,
    'locales': True,
    'tests': True,
    'app.py': False,
    'launcher.py': False,
    'updater.py': False,
    'loggers.py': False,
    'logger_conf.py': False,
    'exit_codes.py': False,
    'utils.py': False,
    'pyproject.toml': False,
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
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
    except:
        is_admin = False

    if not is_admin:
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None,
            'runas',
            sys.executable,
            params,
            None,
            1,
        )
        sys.exit(0)


def self_check():
    for name, is_dir in TO_MOVE.items():
        if not os.path.exists(name):
            logger.critical(f'Cannot find {name!r}. Abort.')
            exit(1)
        if os.path.isdir(name) != is_dir:
            logger.critical(
                f'{name!r} must be a file. Abort.'
                if not is_dir
                else f'{name!r} must be a directory.',
            )
            exit(1)


def get_dependencies() -> list[str]:
    if not os.path.exists('pyproject.toml'):
        logger.warning('pyproject.toml not found. Skipping dependencies installation.')
        return []

    try:
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            data = tomllib.loads(f.read())
    except:
        logger.critical('Unable to load pyproject.toml.', exc_info=True)
        exit(1)

    deps = data.get('project', {}).get('dependencies', [])
    return deps


def install_dependencies() -> None:
    deps = get_dependencies()
    if not deps:
        return

    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'], check=True)
    except subprocess.CalledProcessError:
        try:
            subprocess.run([sys.executable, '-m', 'ensurepip', '--upgrade'], check=True)
        except Exception:
            logger.critical('An error occurred while installing pip.', exc_info=True)
            exit(1)

    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', *deps], check=True)
    except:
        logger.critical('An error occurred while installing dependencies.', exc_info=True)
        exit(1)


def move_to_releases():
    logger.info(f'Preparing temporary release directory: {TEMP_BOOTSTRAP_PATH}')

    if TEMP_BOOTSTRAP_PATH.exists():
        logger.critical(f'Temporary path {TEMP_BOOTSTRAP_PATH} already exists. Abort.')
        exit(1)

    try:
        TEMP_BOOTSTRAP_PATH.mkdir(parents=True)
    except Exception:
        logger.critical(f'Cannot create temporary directory {TEMP_BOOTSTRAP_PATH}', exc_info=True)
        exit(1)

    for name, is_dir in TO_MOVE.items():
        src = Path(name)
        dst = TEMP_BOOTSTRAP_PATH / name

        try:
            if is_dir:
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        except Exception:
            logger.critical(f'Failed to copy {name} to temporary release.', exc_info=True)
            shutil.rmtree(TEMP_BOOTSTRAP_PATH, ignore_errors=True)
            exit(1)

    backup = None
    if BOOTSTRAP_PATH.exists():
        backup = BOOTSTRAP_PATH.with_name('bootstrap_old')
        logger.info('Backup current bootstrap before replacement.')
        try:
            if backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
            os.replace(str(BOOTSTRAP_PATH), str(backup))
        except Exception:
            logger.critical('Failed to backup existing bootstrap.', exc_info=True)
            shutil.rmtree(TEMP_BOOTSTRAP_PATH, ignore_errors=True)
            exit(1)

    try:
        os.replace(str(TEMP_BOOTSTRAP_PATH), str(BOOTSTRAP_PATH))
        logger.info('Bootstrap successfully updated.')
    except Exception:
        logger.critical('Failed to replace bootstrap with new release.', exc_info=True)
        if BOOTSTRAP_PATH.exists():
            shutil.rmtree(BOOTSTRAP_PATH, ignore_errors=True)
        if backup is not None and backup.exists():
            os.replace(str(backup), str(BOOTSTRAP_PATH))
        exit(1)

    if backup is not None and backup.exists():
        shutil.rmtree(backup, ignore_errors=True)

    return BOOTSTRAP_PATH


def update_current_link():
    temp_link = CURRENT_RELEASE_PATH.with_name('current_tmp')

    if temp_link.exists() or temp_link.is_symlink():
        temp_link.unlink(missing_ok=True)

    try:
        if IS_WINDOWS:
            subprocess.run(
                ['cmd', '/c', 'mklink', '/J', str(temp_link), str(BOOTSTRAP_PATH)],
                check=True,
                shell=True,
            )
        else:
            os.symlink(BOOTSTRAP_PATH, temp_link)
    except Exception:
        logger.critical('Failed to create temporary current link.', exc_info=True)
        exit(1)

    try:
        if CURRENT_RELEASE_PATH.exists() or CURRENT_RELEASE_PATH.is_symlink():
            CURRENT_RELEASE_PATH.unlink()
        os.replace(temp_link, CURRENT_RELEASE_PATH)
        logger.info('Current link successfully updated.')
    except Exception:
        logger.critical('Failed to replace current link.', exc_info=True)
        exit(1)


def launch():
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([str(CURRENT_RELEASE_PATH), env.get('PYTHONPATH', '')])
    env['FPH_LOCALES'] = str(LOCALES_PATH)
    env['RELEASES_PATH'] = str(RELEASES_PATH)

    cmd = [sys.executable, LAUNCHER_PATH]
    if args.token:
        cmd.extend(['-t', args.token])

    if IS_WINDOWS:
        subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin, env=env)
    else:
        os.execv(sys.executable, cmd)


def main():
    if IS_WINDOWS:
        elevate()

    self_check()
    if '--skip-pip' not in sys.argv:
        install_dependencies()

    move_to_releases()
    update_current_link()
    logger.info('FunPay Hub successfully installed! Launching...')
    launch()
    exit(0)


if __name__ == '__main__':
    main()
