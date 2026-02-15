from __future__ import annotations

import os
import sys
import uuid
import shutil
import asyncio
import tomllib
import zipfile
import subprocess
from dataclasses import dataclass
from pathlib import Path

import aiohttp
from aiohttp import ClientSession
from packaging.version import Version

from funpayhub.utils import IS_WINDOWS
from funpayhub.loggers import updater as logger

from funpayhub.lib.translater import _en


REPO = 'funpayhub/funpayhub'
RELEASES_PATH = Path(os.environ.get('RELEASES_PATH', 'releases')).absolute()
UPDATE_PATH = RELEASES_PATH / '.update'


@dataclass
class UpdateInfo:
    version: Version
    title: str
    description: str
    url: str


async def check_updates(current_version: Version | str) -> UpdateInfo | None:
    if isinstance(current_version, str):
        current_version = Version(current_version)

    logger.info(_en('Fetching releases...'))

    try:
        async with ClientSession() as s:
            result = await s.get(
                f'https://api.github.com/repos/{REPO}/releases',
                headers={'Accept': 'application/vnd.github+json'},
            )
            data = await result.json()
    except:
        logger.error(_en('An error occurred while fetching releases.'), exc_info=True)
        raise

    if not data:
        logger.info(_en('No releases available.'))
        return None

    latest = data[0]
    latest_version = latest['tag_name'].replace('v', '').strip()
    if not latest_version:
        logger.info(_en('No releases available.'))
        return None

    latest_version = Version(latest_version)
    if latest_version <= current_version:
        logger.info(_en('No releases available.'))
        return None

    logger.info(_en('New release %s available.'), str(latest_version))
    return UpdateInfo(
        version=latest_version,
        title=latest['name'],
        description=latest['body'],
        url=latest['zipball_url'],
    )


async def _download_update(url: str, dst: str) -> None:
    async with ClientSession() as s:
        async with s.get(url) as response:
            response.raise_for_status()
            with open(dst, 'wb') as f:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)


async def download_update(url: str, dst: str = '.update.zip') -> None:
    logger.info(_en('Downloading update from %s'), url)
    try:
        await _download_update(url, dst)
    except aiohttp.ClientResponseError as e:
        logger.error(_en('Unexpected status code while downloading update: %d.'), e.status)
        raise
    except asyncio.TimeoutError:
        logger.error(_en('Timeout error while downloading updated.'))
        raise
    except Exception:
        logger.error(_en('Unexpected error while downloading an updated.'), exc_info=True)
        raise


def _install_update(update_archive: str) -> None:
    temp_update_path = UPDATE_PATH.with_name(f'.update_{uuid.uuid4().hex}')
    backup = None

    if temp_update_path.exists():
        logger.critical('Temporary update path %s already exists. Abort.', temp_update_path)
        raise RuntimeError('Temporary update path already exists.')

    try:
        temp_update_path.mkdir(parents=True)
    except Exception:
        logger.critical(
            'Cannot create temporary update directory %s.',
            temp_update_path,
            exc_info=True,
        )
        raise

    with zipfile.ZipFile(update_archive, mode='r') as zip:
        for info in zip.infolist():
            if info.is_dir():
                continue

            new_path = temp_update_path / Path(*Path(info.filename).parts[1:])
            os.makedirs(new_path.parent, exist_ok=True)
            with zip.open(info.filename, 'r') as src, open(new_path, 'wb') as dst:
                shutil.copyfileobj(src, dst)

    if UPDATE_PATH.exists():
        backup = UPDATE_PATH.with_name('.update_old')
        logger.info('Backup current update path before replacement.')
        try:
            if backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
            os.replace(str(UPDATE_PATH), str(backup))
        except Exception:
            logger.critical('Failed to backup existing update path.', exc_info=True)
            shutil.rmtree(temp_update_path, ignore_errors=True)
            raise

    try:
        os.replace(str(temp_update_path), str(UPDATE_PATH))
    except Exception:
        logger.critical('Failed to replace update path with new update.', exc_info=True)
        if UPDATE_PATH.exists():
            shutil.rmtree(UPDATE_PATH, ignore_errors=True)
        if backup is not None and backup.exists():
            os.replace(str(backup), str(UPDATE_PATH))
        raise

    if backup is not None and backup.exists():
        shutil.rmtree(backup, ignore_errors=True)


def install_update(update_archive: str) -> None:
    logger.info(_en('Installing update to %s ...'), UPDATE_PATH)
    try:
        _install_update(update_archive)
    except:
        logger.error(
            _en('Unexpected error while installing update to %s.'),
            UPDATE_PATH,
            exc_info=True,
        )
        raise


def parse_pyproject(update_path: Path) -> tuple[Version, list[str]]:
    pyproject_path = update_path / 'pyproject.toml'
    if not pyproject_path.exists():
        logger.critical('Missing %s in update.', 'pyproject.toml')
        raise FileNotFoundError(pyproject_path)

    try:
        with open(pyproject_path, 'rb') as src:
            pyproject = tomllib.load(src)
    except Exception:
        logger.critical('Failed to read %s.', pyproject_path, exc_info=True)
        raise

    deps = pyproject.get('project', {}).get('dependencies', [])

    version = pyproject.get('project', {}).get('version')
    if not version:
        logger.critical('Update pyproject.toml has no project.version.')
        raise RuntimeError('Missing project.version in pyproject.toml.')

    try:
        return Version(version), deps
    except Exception:
        logger.critical('Invalid update version: %r.', version, exc_info=True)
        raise


def install_dependencies(deps: list[str]) -> None:
    if not deps:
        return

    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'], check=True)
    except Exception:
        subprocess.run([sys.executable, '-m', 'ensurepip', '--upgrade'], check=True)

    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', *deps], check=True)
    except Exception:
        logger.error('Failed to install dependencies.', exc_info=True)
        raise


def apply_update(update_path: Path) -> Version:
    logger.info('Applying update from %s.', update_path)

    if not update_path.exists():
        logger.critical('Update path %s does not exist.', update_path)
        raise FileNotFoundError(update_path)
    if not update_path.is_dir():
        logger.critical('Update path %s is not a directory.', update_path)
        raise NotADirectoryError(update_path)
    if update_path.is_symlink():
        logger.critical('Update path %s must not be a symlink.', update_path)
        raise RuntimeError('Update path is a symlink.')

    version, deps = parse_pyproject(update_path)
    install_dependencies(deps)

    target_path = update_path.parent / str(version)
    if target_path.exists():
        backup = target_path.with_name(f'{version}_old')
        logger.warning('Target release %s already exists. Backing up to %s.', target_path, backup)
        try:
            if backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
            os.replace(str(target_path), str(backup))
        except Exception:
            logger.critical('Failed to backup existing release %s.', target_path, exc_info=True)
            raise
    else:
        backup = None

    try:
        update_path.rename(target_path)
    except Exception:
        logger.critical('Failed to move update into %s.', target_path, exc_info=True)
        if backup is not None and backup.exists():
            os.replace(str(backup), str(target_path))
        raise

    current_link = update_path.parent / 'current'
    temp_link = current_link.with_name('current_tmp')
    if temp_link.exists() or temp_link.is_symlink():
        if temp_link.is_dir() and not temp_link.is_symlink():
            shutil.rmtree(temp_link, ignore_errors=True)
        else:
            temp_link.unlink(missing_ok=True)

    try:
        if IS_WINDOWS:
            subprocess.run(
                ['cmd', '/c', 'mklink', '/J', str(temp_link), str(target_path)],
                check=True,
                shell=True,
            )
        else:
            os.symlink(target_path, temp_link)
    except Exception:
        logger.critical('Failed to create temporary current link.', exc_info=True)
        raise

    try:
        if current_link.exists() or current_link.is_symlink():
            if current_link.is_dir() and not current_link.is_symlink():
                shutil.rmtree(current_link, ignore_errors=True)
            else:
                current_link.unlink()
        os.replace(temp_link, current_link)
        logger.info('Current link successfully updated.')
    except Exception:
        logger.critical('Failed to replace current link.', exc_info=True)
        raise

    return version
