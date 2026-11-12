"""First installation of FunPay Hub.

Installs the sources this file is located in as the first release and starts the launcher:

1. copies the sources into ``releases/<version>``;
2. creates ``releases/<version>/.venv`` with ``uv sync``;
3. writes the ``.installed`` marker and ``releases/state.json``;
4. copies ``launcher.py`` into the working directory (if the sources are elsewhere);
5. runs the launcher with the given arguments.

Later releases are installed by the app itself. If a release is already installed,
only starts the launcher.

Usage: ``python bootstrap.py [launcher args...]`` from the working directory.
Requires ``uv`` (``$HUBPLATFORM_UV_BIN`` or ``PATH``).
"""

from __future__ import annotations

import os
import sys
import shutil
import secrets
import tomllib
import subprocess
from pathlib import Path
from datetime import UTC, datetime

import launcher
from launcher import (
    SCHEMA,
    VENV_DIR,
    MARKER_FILE,
    TEMP_PREFIX,
    State,
    logger,
    setup_logging,
    write_json_atomic,
    replace_with_retry,
)


SOURCE_DIR = Path(__file__).resolve().parent

EXCLUDE = shutil.ignore_patterns(
    # VCS / tooling
    '.git',
    '.github',
    '.idea',
    '.vscode',
    '.agents',
    '.mypy_cache',
    '.ruff_cache',
    '.pytest_cache',
    '__pycache__',
    '*.log',
    # environments and working dir data (if the sources are the working dir)
    '.venv',
    'venv',
    'env',
    'releases',
    'backups',
    'storage',
    'config',
    'logs',
    'plugins',
)


def find_uv() -> str:
    uv = os.environ.get('HUBPLATFORM_UV_BIN') or shutil.which('uv')
    if uv is None:
        raise FileNotFoundError('uv is not installed: https://docs.astral.sh/uv/')
    return uv


def install(releases_dir: Path) -> None:
    with (SOURCE_DIR / 'pyproject.toml').open('rb') as f:
        version = str(tomllib.load(f)['project']['version'])

    target = releases_dir / version
    if (target / MARKER_FILE).is_file():
        logger.info('Release %s is already installed.', version)
    else:
        logger.info('Installing release %s into %s.', version, target)
        releases_dir.mkdir(parents=True, exist_ok=True)
        temp = releases_dir / f'{TEMP_PREFIX}{version}-{secrets.token_hex(8)}'
        try:
            shutil.copytree(SOURCE_DIR, temp, ignore=EXCLUDE)
            if target.exists():
                shutil.rmtree(target)
            replace_with_retry(temp, target)
        finally:
            shutil.rmtree(temp, ignore_errors=True)

        lock_args = ['--frozen'] if (target / 'uv.lock').is_file() else []
        env = os.environ | {'UV_PROJECT_ENVIRONMENT': str(target / VENV_DIR)}
        env.pop('VIRTUAL_ENV', None)
        subprocess.run(
            [find_uv(), 'sync', '--no-dev', *lock_args],
            cwd=target,
            env=env,
            check=True,
        )

        write_json_atomic(
            target / MARKER_FILE,
            {
                'schema': SCHEMA,
                'version': version,
                'sha256': None,
                'installed_at': datetime.now(UTC).isoformat(),
            },
        )

    state_file = releases_dir / launcher.STATE_FILE
    if not state_file.exists():
        write_json_atomic(state_file, State(current=version).to_json())
    logger.info('Release %s installed.', version)


def main() -> int:
    workdir = Path(os.environ.get('HUBPLATFORM_WORKDIR') or os.getcwd()).resolve()
    releases_dir = Path(os.environ.get('HUBPLATFORM_RELEASES_DIR') or workdir / 'releases')

    os.chdir(workdir)
    setup_logging(workdir / 'logs')
    try:
        install(releases_dir.resolve())
    except Exception:
        logger.critical('Installation failed.', exc_info=True)
        return 1

    installed_launcher = workdir / 'launcher.py'
    if installed_launcher.resolve() != Path(launcher.__file__).resolve():
        shutil.copy2(launcher.__file__, installed_launcher)

    # `launcher.main` sets up logging again.
    logger.handlers.clear()
    return launcher.main(sys.argv[1:])


if __name__ == '__main__':
    sys.exit(main())
