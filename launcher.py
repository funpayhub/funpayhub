"""FunPay Hub launcher.

Runs the current release, restarts it and switches releases. Uses only the standard library
and runs on its own Python (``launcher/python``), independent of the app runtimes.

The launcher is installed into the working directory once and is not updated together with
the app. It talks to the app only through the launcher protocol (exit codes, environment
variables and files), described in ``hubplatform.runtime`` and
``hubplatform.updates.releases``. Changes must stay compatible with installed launchers and
apps, or bump ``LAUNCHER_PROTOCOL``.

A newer launcher shipped with a release replaces this file after the release confirmed it
starts; it takes effect on the next launcher start.

Working directory::

    launcher/       python/ + this file
    releases/       <version>/ (app), state.json, staged.json, result.json
    runtimes/       <runtime id>/ (Python + third-party packages)
    envs/           <runtime id>/ (optional venv on top of the runtime, plugin packages)
    backups/        app data saved before the last release switch
    storage/ config/ logs/ plugins/

Usage, from the working directory::

    python launcher.py [--safe] [app args...]
    python launcher.py --install latest|<manifest url> [--safe] [app args...]
        first installation: download and install a release, then run it
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import shutil
import hashlib
import logging
import secrets
import tarfile
import zipfile
import argparse
import platform
import subprocess
import urllib.request
from typing import Any
from dataclasses import field, asdict, dataclass
from pathlib import Path, PurePosixPath
from datetime import UTC, datetime
from logging.handlers import TimedRotatingFileHandler


LAUNCHER_VERSION = 1
"""Version of this file. Bump on every change, so releases can replace installed launchers."""

LAUNCHER_PROTOCOL = 1
"""Launcher protocol version (see ``hubplatform.runtime``)."""

SCHEMA = 1
"""Version of the files format."""

GITHUB_REPO = 'funpayhub/funpayhub'
"""Repository ``--install latest`` installs from."""
MANIFEST_ASSET = 'manifest.json'

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

STATE_FILE = 'state.json'
STAGED_FILE = 'staged.json'
RESULT_FILE = 'result.json'
RELEASE_FILE = 'release.json'
RUNTIME_FILE = 'runtime.json'
HEALTH_FILE = '.health'
MARKER_FILE = '.installed'
TEMP_PREFIX = '.tmp-'

IS_WINDOWS = os.name == 'nt'

logger = logging.getLogger('launcher')


# ---------------------------------------------
# |                   Files                   |
# ---------------------------------------------
def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None


def replace_with_retry(src: Path, dst: Path, attempts: int = 10) -> None:
    """``os.replace`` that tolerates short-living locks of antivirus / indexers on Windows."""
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


def remove_tree(path: Path) -> None:
    if path.is_symlink() or (IS_WINDOWS and path.is_junction()):
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def mark_installed(directory: Path, sha256: str) -> None:
    write_json_atomic(
        directory / MARKER_FILE,
        {'schema': SCHEMA, 'sha256': sha256, 'installed_at': datetime.now(UTC).isoformat()},
    )


def runtime_python(runtime_dir: Path) -> Path:
    if IS_WINDOWS:
        return runtime_dir / 'python' / 'python.exe'
    return runtime_dir / 'python' / 'bin' / 'python3'


def venv_python(venv: Path) -> Path:
    return venv / 'Scripts' / 'python.exe' if IS_WINDOWS else venv / 'bin' / 'python'


def current_platform() -> str | None:
    """python-build-standalone name of this machine's platform, ``None`` if unsupported."""
    machine = platform.machine().lower()
    arch = {'amd64': 'x86_64', 'x86_64': 'x86_64', 'arm64': 'aarch64', 'aarch64': 'aarch64'}
    if machine not in arch:
        return None
    if sys.platform == 'win32':
        return f'{arch[machine]}-pc-windows-msvc'
    if sys.platform.startswith('linux') and platform.libc_ver()[0] == 'glibc':
        return f'{arch[machine]}-unknown-linux-gnu'
    return None


@dataclass
class State:
    current: str
    previous: str | None = None
    pending: bool = False
    attempts: int = 0
    failed: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Any) -> State:
        return cls(
            current=str(data['current']),
            previous=data.get('previous') or None,
            pending=bool(data.get('pending', False)),
            attempts=int(data.get('attempts', 0)),
            failed=[str(i) for i in data.get('failed', [])],
        )

    def to_json(self) -> dict[str, Any]:
        return {'schema': SCHEMA, **asdict(self)}


@dataclass(frozen=True)
class Release:
    """``release.json`` of an installed release."""

    version: str
    runtime: str
    entrypoint: str
    pythonpath: tuple[str, ...]

    @classmethod
    def read(cls, release_dir: Path) -> Release:
        data = read_json(release_dir / RELEASE_FILE)
        if data is None:
            raise ValueError(f'{release_dir} has no {RELEASE_FILE}.')
        for value in (data['entrypoint'], *data['pythonpath']):
            path = PurePosixPath(value)
            if path.is_absolute() or '..' in path.parts or ':' in value or '\\' in value:
                raise ValueError(f'Invalid path in {RELEASE_FILE}: {value!r}.')
        return cls(
            version=str(data['version']),
            runtime=str(data['runtime']),
            entrypoint=str(data['entrypoint']),
            pythonpath=tuple(str(i) for i in data['pythonpath']),
        )


# ---------------------------------------------
# |                 Launcher                  |
# ---------------------------------------------
class Launcher:
    def __init__(
        self,
        workdir: Path,
        app_args: list[str],
        safe: bool = False,
        snapshot_dirs: tuple[str, ...] = DEFAULT_SNAPSHOT_DIRS,
    ) -> None:
        self.workdir = workdir
        self.releases_dir = workdir / 'releases'
        self.runtimes_dir = workdir / 'runtimes'
        self.envs_dir = workdir / 'envs'
        self.backups_dir = workdir / 'backups'
        self.app_args = app_args
        self.safe = safe
        self.snapshot_dirs = snapshot_dirs

    # ---------- paths / files ----------
    def release_dir(self, version: str) -> Path:
        return self.releases_dir / version

    def runtime_dir(self, runtime_id: str) -> Path:
        return self.runtimes_dir / runtime_id

    def is_installed(self, version: str) -> bool:
        """Whether the release and its runtime are installed."""
        release_dir = self.release_dir(version)
        if not (release_dir / MARKER_FILE).is_file():
            return False
        try:
            release = Release.read(release_dir)
        except ValueError, KeyError, TypeError:
            logger.error('Release %s is broken.', version, exc_info=True)
            return False
        return (self.runtime_dir(release.runtime) / MARKER_FILE).is_file()

    @property
    def health_file(self) -> Path:
        return self.releases_dir / HEALTH_FILE

    def read_state(self) -> State | None:
        data = read_json(self.releases_dir / STATE_FILE)
        return State.from_json(data) if data is not None else None

    def write_state(self, state: State) -> None:
        write_json_atomic(self.releases_dir / STATE_FILE, state.to_json())

    def write_result(
        self,
        status: str,
        version: str,
        previous: str | None,
        message: str | None = None,
    ) -> None:
        write_json_atomic(
            self.releases_dir / RESULT_FILE,
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
            self.apply_staged()

            state = self.read_state()
            if state is None:
                logger.critical(
                    'No installed release found in %s. Install one with --install latest.',
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

    def start(self, state: State) -> tuple[int | None, bool]:
        """Run the current release until it exits.

        :return: exit code (``None`` if it did not start in time and was killed)
            and whether it confirmed it started (only checked for pending releases).
        """
        release_dir = self.release_dir(state.current)
        release = Release.read(release_dir)
        env_dir = self.envs_dir / release.runtime
        if (env_dir / 'pyvenv.cfg').is_file():
            python = venv_python(env_dir)
        else:
            python = runtime_python(self.runtime_dir(release.runtime))
        args = [*self.app_args, '--safe'] if self.safe else list(self.app_args)

        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ('VIRTUAL_ENV', 'PYTHONHOME', 'PYTHONPATH')
        }
        env.update(
            {
                'PYTHONPATH': os.pathsep.join(str(release_dir / i) for i in release.pythonpath),
                'PYTHONNOUSERSITE': '1',
                'HUBPLATFORM_LAUNCHER_PROTOCOL': str(LAUNCHER_PROTOCOL),
                'HUBPLATFORM_RELEASES_DIR': str(self.releases_dir),
                'HUBPLATFORM_RUNTIMES_DIR': str(self.runtimes_dir),
                'HUBPLATFORM_ENVS_DIR': str(self.envs_dir),
                'HUBPLATFORM_RELEASE': state.current,
                'HUBPLATFORM_RUNTIME': release.runtime,
                'HUBPLATFORM_HEALTH_FILE': str(self.health_file),
            },
        )

        self.health_file.unlink(missing_ok=True)
        logger.info(
            'Starting release %s (runtime %s) with args %s.',
            state.current,
            release.runtime,
            args,
        )
        try:
            process = subprocess.Popen(
                [str(python), '-s', str(release_dir / release.entrypoint), *args],
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
        """Stop the app. On Ctrl+C the app received it too, so first just wait for it."""
        # A second Ctrl+C or a timeout terminates the app.
        # (No `except (A, B)`: the formatter would drop the parentheses, Python < 3.14 fails.)
        try:
            return process.wait(timeout=STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            pass
        except KeyboardInterrupt:
            pass
        process.terminate()
        try:
            return process.wait(timeout=STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.wait()

    # ---------- switching releases ----------
    def apply_staged(self) -> None:
        """Switch to the release the app staged before exiting with ``UPDATE``."""
        staged_file = self.releases_dir / STAGED_FILE
        try:
            data = read_json(staged_file)
        except ValueError:
            logger.error('Invalid %s, ignoring it.', staged_file, exc_info=True)
            staged_file.unlink(missing_ok=True)
            return
        if data is None:
            return

        version = str(data.get('version', ''))
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
            self.snapshot(state.current)
            self.write_state(
                State(
                    current=version,
                    previous=state.current,
                    pending=True,
                    failed=[i for i in state.failed if i != version],
                ),
            )
            self.write_result('updated', version, previous)
        except Exception as e:
            logger.error('Unable to switch to release %r.', version, exc_info=True)
            self.write_result('failed', version, previous, str(e))
        finally:
            staged_file.unlink(missing_ok=True)

        self.remove_unused()

    def confirm(self, state: State) -> None:
        logger.info('Release %s started successfully.', state.current)
        state.pending = False
        state.attempts = 0
        self.write_state(state)
        try:
            self.update_self(self.release_dir(state.current))
        except Exception:
            logger.error('Unable to update the launcher.', exc_info=True)

    def rollback(self, state: State) -> bool:
        failed, previous = state.current, state.previous
        if previous is None or not self.is_installed(previous):
            logger.critical(
                'Release %s does not start and there is no previous release to roll back to.',
                failed,
            )
            return False

        logger.warning('Rolling back from release %s to %s.', failed, previous)
        try:
            self.restore(previous, failed)
        except Exception:
            logger.critical('Unable to restore app data.', exc_info=True)
            return False

        self.write_state(
            State(
                current=previous,
                failed=[*(i for i in state.failed if i != failed), failed],
            ),
        )
        self.write_result(
            'rolled_back',
            failed,
            previous,
            f'Release {failed} failed to start {state.attempts} times.',
        )
        return True

    def remove_unused(self) -> None:
        """Remove releases except the current and the previous ones, and runtimes / envs
        they do not use. Leftovers of interrupted installations are removed by the app."""
        state = self.read_state()
        if state is None:
            return
        keep = {state.current, state.previous}
        used_runtimes = set()
        for version in keep:
            if version is not None and self.is_installed(version):
                used_runtimes.add(Release.read(self.release_dir(version)).runtime)

        to_remove = [
            i
            for i in self.releases_dir.iterdir()
            if i.name not in keep and (i / MARKER_FILE).is_file()
        ]
        for parent in (self.runtimes_dir, self.envs_dir):
            if parent.is_dir():
                to_remove += [
                    i
                    for i in parent.iterdir()
                    if i.is_dir()
                    and not i.name.startswith('.')
                    and i.name not in used_runtimes
                    and ((i / MARKER_FILE).is_file() or (i / 'pyvenv.cfg').is_file())
                ]
        for i in to_remove:
            logger.info('Removing unused %s.', i.relative_to(self.workdir))
            try:
                remove_tree(i)
            except OSError:
                logger.warning('Unable to remove %s.', i, exc_info=True)

    # ---------- app data ----------
    def snapshot(self, version: str) -> None:
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

    def restore(self, version: str, failed: str) -> None:
        """Restore app data saved before switching from ``version``.

        Data of the ``failed`` release is moved to ``backups/<failed>.failed``.
        """
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

    # ---------- self update ----------
    def update_self(self, release_dir: Path) -> None:
        """Replace this file with a newer launcher shipped with the release."""
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

    # ---------- first installation ----------
    def install(self, source: str) -> None:
        """Install a release from its update manifest (URL or ``latest``) as the current one.

        The app installs further releases itself (``hubplatform.updates.ReleaseInstaller``).
        """
        if self.read_state() is not None:
            raise RuntimeError('FunPay Hub is already installed, it updates itself.')

        manifest_url = source if source != 'latest' else latest_manifest_url()
        logger.info('Installing from %s.', manifest_url)
        manifest = json.loads(fetch(manifest_url))
        if manifest.get('schema') != SCHEMA:
            raise ValueError(f'Unsupported manifest schema {manifest.get("schema")}.')
        if manifest['launcher_protocol'] > LAUNCHER_PROTOCOL:
            raise RuntimeError('This release needs a newer launcher, download it again.')

        version = str(manifest['version'])
        target_platform = current_platform()
        runtime_id = str(manifest['runtime']['id'])
        runtime_asset = manifest['runtime']['assets'].get(target_platform or '')
        if runtime_asset is None:
            raise RuntimeError(f'FunPay Hub is not available for {target_platform or "this OS"}.')

        downloads = self.releases_dir / '.downloads'
        downloads.mkdir(parents=True, exist_ok=True)
        runtime_dir = self.runtime_dir(runtime_id)
        if not (runtime_dir / MARKER_FILE).is_file():
            archive = download_asset(runtime_asset, downloads / f'runtime-{runtime_id}.tar.gz')
            temp = self.runtimes_dir / f'{TEMP_PREFIX}{runtime_id}-{secrets.token_hex(8)}'
            try:
                temp.mkdir(parents=True)
                with tarfile.open(archive, 'r:gz') as tar:
                    tar.extractall(temp, filter='data')
                if read_json(temp / RUNTIME_FILE).get('id') != runtime_id:
                    raise ValueError(f'Runtime archive is not {runtime_id}.')
                remove_tree(runtime_dir)
                replace_with_retry(temp, runtime_dir)
                mark_installed(runtime_dir, runtime_asset['sha256'])
            finally:
                remove_tree(temp)
                archive.unlink(missing_ok=True)

        archive = download_asset(manifest['app'], downloads / f'app-{version}.zip')
        release_dir = self.release_dir(version)
        temp = self.releases_dir / f'{TEMP_PREFIX}{version}-{secrets.token_hex(8)}'
        try:
            with zipfile.ZipFile(archive) as z:
                for name in z.namelist():
                    path = PurePosixPath(name)
                    if path.is_absolute() or '..' in path.parts or ':' in name or '\\' in name:
                        raise ValueError(f'Archive contains unsafe path: {name}.')
                temp.mkdir(parents=True)
                z.extractall(temp)
            release = Release.read(temp)
            if release.version != version or release.runtime != runtime_id:
                raise ValueError('App archive does not match the manifest.')
            remove_tree(release_dir)
            replace_with_retry(temp, release_dir)
            mark_installed(release_dir, manifest['app']['sha256'])
        finally:
            remove_tree(temp)
            archive.unlink(missing_ok=True)

        self.write_state(State(current=version))
        logger.info('FunPay Hub %s installed.', version)


def fetch(url: str, limit: int = 1024 * 1024) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': 'funpayhub-launcher'})
    with urllib.request.urlopen(request, timeout=60) as response:
        data: bytes = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f'{url} is too large.')
    return data


def latest_manifest_url() -> str:
    repo = os.environ.get('HUBPLATFORM_GITHUB_REPO', GITHUB_REPO)
    release = json.loads(fetch(f'https://api.github.com/repos/{repo}/releases/latest'))
    for asset in release.get('assets', []):
        if asset.get('name') == MANIFEST_ASSET:
            return str(asset['browser_download_url'])
    raise RuntimeError(f'Latest release of {repo} has no {MANIFEST_ASSET}.')


def download_asset(asset: dict[str, Any], destination: Path) -> Path:
    logger.info('Downloading %s (%d MB).', asset['url'], asset['size'] // 1024 // 1024)
    request = urllib.request.Request(asset['url'], headers={'User-Agent': 'funpayhub-launcher'})
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(request, timeout=60) as response, destination.open('wb') as f:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
            f.write(chunk)
    if size != asset['size'] or digest.hexdigest() != asset['sha256']:
        destination.unlink(missing_ok=True)
        raise ValueError(f'{asset["url"]}: downloaded file does not match the manifest.')
    return destination


# ---------------------------------------------
# |                   Entry                   |
# ---------------------------------------------
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
    parser.add_argument('--install', metavar='latest|URL')
    args, app_args = parser.parse_known_args(argv)

    workdir = Path(os.environ.get('HUBPLATFORM_WORKDIR') or os.getcwd()).resolve()
    snapshot_dirs = os.environ.get('HUBPLATFORM_SNAPSHOT_DIRS')

    os.chdir(workdir)
    setup_logging(workdir / 'logs')
    logger.info('Launcher %d started in %s.', LAUNCHER_VERSION, workdir)

    launcher = Launcher(
        workdir=workdir,
        app_args=app_args,
        safe=args.safe,
        snapshot_dirs=(
            tuple(i for i in snapshot_dirs.split(os.pathsep) if i)
            if snapshot_dirs is not None
            else DEFAULT_SNAPSHOT_DIRS
        ),
    )
    try:
        if args.install is not None:
            try:
                launcher.install(args.install)
            except Exception:
                logger.critical('Installation failed.', exc_info=True)
                return 1
        return launcher.run()
    except KeyboardInterrupt:
        logger.info('Interrupted.')
        return 0


if __name__ == '__main__':
    sys.exit(main())
