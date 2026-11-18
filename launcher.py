from __future__ import annotations

import os
import re
import sys
import json
import time
import shutil
import logging
import secrets
import tomllib
import argparse
import subprocess
from typing import Any
from dataclasses import field, asdict, dataclass
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


LAUNCHER_VERSION = 1
"""Version of this file. Bump on every change, so releases can replace installed launchers."""

LAUNCHER_PROTOCOL = 1
"""Launcher protocol version (see ``hubplatform.runtime``)."""

SCHEMA = 1
"""Version of the releases files format."""

SHUTDOWN = 0
RESTART = 100
RESTART_SAFE = 101
RESTART_NORMAL = 102
UPDATE = 103
ACTION_CODES = frozenset({SHUTDOWN, RESTART, RESTART_SAFE, RESTART_NORMAL, UPDATE})

HEALTH_TIMEOUT = 5 * 60
"""Seconds a just switched to release has to signal it started."""
MAX_START_ATTEMPTS = 2
"""Failed starts of a just switched to release before rolling back."""
STOP_TIMEOUT = 60
DEFAULT_SNAPSHOT_DIRS = ('storage', 'config')
"""Working dir subdirectories saved before switching releases and restored on rollback."""

LAUNCHER_STATE_FILE = '.launcher_state'
UPDATE_INFO_FILE = '.update_info'
UPDATE_RESULT_FILE = '.update_result'
HEALTH_FILE = '.health'
MARKER_FILE = '.installed'
VENV_DIR = '.venv'
TEMP_PREFIX = '.tmp-'

IS_WINDOWS = os.name == 'nt'

logger = logging.getLogger('launcher')


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None


def replace_with_retry(src: Path, dst: Path, attempts: int = 10) -> None:
    for attempt in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.5)


def write_json_atomic(path: Path, data: Any) -> None:
    temp = path.with_name(f'{path.name}.{secrets.token_hex(8)}.tmp')
    try:
        temp.write_text(json.dumps(data, indent=2), encoding='utf-8')
        replace_with_retry(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def venv_python(venv: Path) -> Path:
    return venv / 'Scripts' / 'python.exe' if IS_WINDOWS else venv / 'bin' / 'python'


def release_entrypoint(release_dir: Path) -> str:
    with (release_dir / 'pyproject.toml').open('rb') as f:
        data = tomllib.load(f)
    return str(
        data.get('tool', {})
        .get('hubplatform', {})
        .get('release', {})
        .get('entryporint', 'app.py'),
    )


def remove_tree(path: Path) -> None:
    if path.is_symlink() or (IS_WINDOWS and path.is_junction()):
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


@dataclass(kw_only=True)
class LauncherState:
    schema: int = field(default=SCHEMA)
    current: str
    previous: str | None = None
    pending: bool = False
    attempts: int = 0
    failed: list[str] = field(default_factory=list)


class Launcher:
    def __init__(
        self,
        workdir: Path,
        releases_dir: Path,
        app_args: list[str],
        safe: bool = False,
        snapshot_dirs: tuple[str, ...] = DEFAULT_SNAPSHOT_DIRS,
    ) -> None:
        self.workdir = workdir
        self.releases_dir = releases_dir
        self.backups_dir = workdir / 'backups'
        self.app_args = app_args
        self.safe = safe
        self.snapshot_dirs = snapshot_dirs

    def release_dir(self, version: str) -> Path:
        return self.releases_dir / version

    def is_installed(self, version: str) -> bool:
        return (self.release_dir(version) / MARKER_FILE).is_file()

    @property
    def health_file(self) -> Path:
        return self.releases_dir / HEALTH_FILE

    def read_state(self) -> LauncherState | None:
        data = read_json(self.releases_dir / LAUNCHER_STATE_FILE)
        return None if data is None else LauncherState(**data)

    def write_state(self, state: LauncherState) -> None:
        write_json_atomic(self.releases_dir / LAUNCHER_STATE_FILE, asdict(state))

    def write_update_result(
        self,
        status: str,
        version: str,
        previous: str | None,
        message: str | None = None,
    ) -> None:
        write_json_atomic(
            self.releases_dir / UPDATE_RESULT_FILE,
            {
                'schema': SCHEMA,
                'status': status,
                'version': version,
                'previous': previous,
                'message': message,
            },
        )

    # ---------- main loop ----------
    def run(self) -> int:
        while True:
            self.apply_update()

            state = self.read_state()
            if state is None:
                logger.critical(
                    'No installed release found in %s. Run bootstrap.py first.',
                    self.releases_dir,
                )
                return 1
            if not self.is_installed(state.current):
                logger.critical('Current release %s is not installed.', state.current)
                return 1

            code, confirmed = self.start(state)

            if state.pending and not confirmed and code not in ACTION_CODES:
                state.attempts += 1
                logger.error(
                    'Release %s failed to start (attempt %d of %d).',
                    state.current,
                    state.attempts,
                    MAX_START_ATTEMPTS,
                )
                if state.attempts < MAX_START_ATTEMPTS:
                    self.write_state(state)
                    continue
                if self.rollback(state):
                    continue
                return code if code is not None else 1

            if code is None:  # unreachable: only pending releases are timed out
                return 1
            if code == SHUTDOWN:
                logger.info('App stopped.')
                return 0
            if code == RESTART:
                logger.info('Restarting the app.')
            elif code == RESTART_SAFE:
                logger.info('Restarting the app in safe mode.')
                self.safe = True
            elif code == RESTART_NORMAL:
                logger.info('Restarting the app in normal mode.')
                self.safe = False
            elif code == UPDATE:
                logger.info('Update requested.')
            else:
                logger.error('App exited with code %d.', code)
                return code

    def start(self, state: LauncherState) -> tuple[int | None, bool]:
        release_dir = self.release_dir(state.current)
        python = venv_python(release_dir / VENV_DIR)
        entrypoint = release_dir / release_entrypoint(release_dir)
        args = [*self.app_args, '--safe'] if self.safe else list(self.app_args)

        env = os.environ.copy()
        env.pop('VIRTUAL_ENV', None)
        env.pop('PYTHONHOME', None)
        env.update(
            {
                'HUBPLATFORM_LAUNCHER_PROTOCOL': str(LAUNCHER_PROTOCOL),
                'HUBPLATFORM_RELEASES_DIR': str(self.releases_dir),
                'HUBPLATFORM_RELEASE': state.current,
                'HUBPLATFORM_HEALTH_FILE': str(self.health_file),
            },
        )

        self.health_file.unlink(missing_ok=True)
        logger.info('Starting release %s with args %s.', state.current, args)
        try:
            process = subprocess.Popen(
                [str(python), str(entrypoint), *args],
                cwd=self.workdir,
                env=env,
            )
        except OSError:
            logger.critical('Unable to start release %s.', state.current, exc_info=True)
            return -1, False

        if not state.pending:
            return self.wait(process), False

        deadline = time.monotonic() + HEALTH_TIMEOUT
        confirmed = False
        while True:
            try:
                code = process.wait(timeout=1)
                break
            except subprocess.TimeoutExpired:
                pass
            except KeyboardInterrupt:
                self.stop(process)
                raise

            if not confirmed and self.health_file.exists():
                confirmed = True
                self.confirm(state)
            if not confirmed and time.monotonic() > deadline:
                logger.error(
                    'Release %s did not start in %d seconds, stopping it.',
                    state.current,
                    HEALTH_TIMEOUT,
                )
                self.stop(process)
                return None, False

        if not confirmed and self.health_file.exists():
            confirmed = True
            self.confirm(state)
        return code, confirmed

    def wait(self, process: subprocess.Popen[bytes]) -> int:
        try:
            return process.wait()
        except KeyboardInterrupt:
            self.stop(process)
            raise

    @staticmethod
    def stop(process: subprocess.Popen[bytes]) -> int:
        try:
            return process.wait(timeout=STOP_TIMEOUT)
        except subprocess.TimeoutExpired, KeyboardInterrupt:
            pass
        process.terminate()
        try:
            return process.wait(timeout=STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.wait()

    def apply_update(self) -> None:
        update_info_file = self.releases_dir / UPDATE_INFO_FILE
        try:
            update_info = read_json(update_info_file)
        except ValueError:
            logger.error('Invalid %s, ignoring it.', update_info_file, exc_info=True)
            update_info_file.unlink(missing_ok=True)
            return
        if update_info is None:
            return

        version = str(update_info.get('version', ''))
        state = self.read_state()
        previous = state.current if state is not None else None
        try:
            if state is None:
                raise RuntimeError('Nothing is installed yet.')
            if not version or not self.is_installed(version):
                raise RuntimeError(f'Release {version!r} is not installed.')
            if version == state.current:
                logger.info('Release %s is already current.', version)
                return

            logger.info('Switching from release %s to %s.', state.current, version)
            self.snapshot_user_data(state.current)
            self.write_state(
                LauncherState(
                    current=version,
                    previous=state.current,
                    pending=True,
                    failed=[i for i in state.failed if i != version],
                ),
            )
            self.write_update_result('updated', version, previous)
        except Exception as e:
            logger.error('Unable to switch to release %r.', version, exc_info=True)
            self.write_update_result('failed', version, previous, str(e))
        finally:
            update_info_file.unlink(missing_ok=True)

        self.remove_old_releases()

    def confirm(self, state: LauncherState) -> None:
        logger.info('Release %s started successfully.', state.current)
        state.pending = False
        state.attempts = 0
        self.write_state(state)
        try:
            self.update_self(self.release_dir(state.current))
        except Exception:
            logger.error('Unable to update the launcher.', exc_info=True)

    def rollback(self, state: LauncherState) -> bool:
        failed, previous = state.current, state.previous
        if previous is None or not self.is_installed(previous):
            logger.critical(
                'Release %s does not start and there is no previous release to roll back to.',
                failed,
            )
            return False

        logger.warning('Rolling back from release %s to %s.', failed, previous)
        try:
            self.restore_user_data(previous, failed)
        except Exception:
            logger.critical('Unable to restore app data.', exc_info=True)
            return False

        self.write_state(
            LauncherState(
                current=previous,
                failed=[*(i for i in state.failed if i != failed), failed],
            ),
        )
        self.write_update_result(
            'rolled_back',
            failed,
            previous,
            f'Release {failed} failed to start {state.attempts} times.',
        )
        return True

    def remove_old_releases(self) -> None:
        state = self.read_state()
        if state is None:
            return
        keep = {state.current, state.previous}
        for i in self.releases_dir.iterdir():
            if i.name in keep or not (i / MARKER_FILE).is_file():
                continue
            logger.info('Removing old release %s.', i.name)
            try:
                remove_tree(i)
            except OSError:
                logger.warning('Unable to remove %s.', i, exc_info=True)

    def snapshot_user_data(self, version: str) -> None:
        """Copy app data to ``backups/<version>``, replacing older backups."""
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        temp = self.backups_dir / f'{TEMP_PREFIX}{secrets.token_hex(8)}'
        try:
            temp.mkdir()
            for name in self.snapshot_dirs:
                src = self.workdir / name
                if src.is_dir():
                    shutil.copytree(src, temp / name, symlinks=True)
            for i in self.backups_dir.iterdir():
                if i != temp:
                    remove_tree(i)
            replace_with_retry(temp, self.backups_dir / version)
        finally:
            if temp.exists():
                shutil.rmtree(temp, ignore_errors=True)
        logger.info('App data saved to %s.', self.backups_dir / version)

    def restore_user_data(self, version: str, failed: str) -> None:
        backup = self.backups_dir / version
        if not backup.is_dir():
            logger.warning('No app data backup for release %s, keeping current data.', version)
            return

        failed_dir = self.backups_dir / f'{failed}.failed'
        remove_tree(failed_dir)
        failed_dir.mkdir(parents=True)
        for name in self.snapshot_dirs:
            current = self.workdir / name
            if current.exists():
                replace_with_retry(current, failed_dir / name)
            if (backup / name).is_dir():
                shutil.copytree(backup / name, current, symlinks=True)
        logger.info('App data restored from %s.', backup)

    def update_self(self, release_dir: Path) -> None:
        source = release_dir / 'launcher.py'
        target = Path(__file__).resolve()
        if not source.is_file() or self.releases_dir in target.parents:
            return

        match = re.search(
            r'^LAUNCHER_VERSION\s*=\s*(\d+)\s*$',
            source.read_text(encoding='utf-8'),
            re.MULTILINE,
        )
        if match is None or int(match.group(1)) <= LAUNCHER_VERSION:
            return

        temp = target.with_name(f'{target.name}.{secrets.token_hex(8)}.tmp')
        try:
            shutil.copy2(source, temp)
            shutil.copy2(target, target.with_name(f'{target.name}.old'))
            replace_with_retry(temp, target)
        finally:
            temp.unlink(missing_ok=True)
        logger.info(
            'Launcher updated from version %d to %s, it will be used after the next start.',
            LAUNCHER_VERSION,
            match.group(1),
        )


def setup_logging(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(
        logging.Formatter('[%(asctime)s] [launcher] [%(levelname)s] %(message)s', '%H:%M:%S'),
    )
    file = TimedRotatingFileHandler(
        logs_dir / 'launcher.log',
        when='D',
        backupCount=10,
        encoding='utf-8',
    )
    file.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(console)
    logger.addHandler(file)
    logger.setLevel(logging.INFO)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--safe', action='store_true')
    args, app_args = parser.parse_known_args(argv)

    workdir = Path(os.environ.get('HUBPLATFORM_WORKDIR') or os.getcwd()).resolve()
    releases_dir = Path(os.environ.get('HUBPLATFORM_RELEASES_DIR') or workdir / 'releases')
    snapshot_dirs = os.environ.get('HUBPLATFORM_SNAPSHOT_DIRS')

    os.chdir(workdir)
    setup_logging(workdir / 'logs')
    logger.info('Launcher %d started in %s.', LAUNCHER_VERSION, workdir)

    launcher = Launcher(
        workdir=workdir,
        releases_dir=releases_dir.resolve(),
        app_args=app_args,
        safe=args.safe,
        snapshot_dirs=(
            tuple(i for i in snapshot_dirs.split(os.pathsep) if i)
            if snapshot_dirs is not None
            else DEFAULT_SNAPSHOT_DIRS
        ),
    )
    try:
        return launcher.run()
    except KeyboardInterrupt:
        logger.info('Interrupted.')
        return 0


if __name__ == '__main__':
    sys.exit(main())
