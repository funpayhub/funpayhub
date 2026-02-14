from __future__ import annotations

import os
import sys
import shutil
import asyncio
import tomllib
import zipfile
import subprocess
from dataclasses import dataclass
from pathlib import Path

import aiohttp
from utils import IS_WINDOWS
from aiohttp import ClientSession
from packaging.version import Version

from funpayhub.loggers import updater as logger

from funpayhub.lib.translater import _en


REPO = 'funpayhub/funpayhub'
UPDATE_EXCLUDE = ['config', 'logs', 'plugins', 'storage']
RELEASES_PATH = Path(os.environ.get('RELEASES_PATH', 'releases'))
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
    if os.path.exists(UPDATE_PATH):
        shutil.rmtree(UPDATE_PATH)
    os.makedirs(UPDATE_PATH, exist_ok=True)

    with zipfile.ZipFile(update_archive, mode='r') as zip:
        for info in zip.infolist():
            if info.is_dir():
                continue

            new_path = UPDATE_PATH / Path(*Path(info.filename).parts[1:])
            os.makedirs(new_path.parent, exist_ok=True)
            with zip.open(info.filename, 'r') as src, open(new_path, 'wb') as dst:
                shutil.copyfileobj(src, dst)


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


def install_dependencies(update_path: Path) -> None:
    if not os.path.exists(update_path / 'pyproject.toml'):
        return

    subprocess.run(
        [
            sys.executable,
            '-m',
            'ensurepip',
            '--upgrade',
        ],
    )

    subprocess.run(
        [
            sys.executable,
            '-m',
            'pip',
            'install',
            '--upgrade',
            'pip',
        ],
    )

    if (update_path / 'requirements.txt').exists(follow_symlinks=True):
        subprocess.run(
            [
                sys.executable,
                '-m',
                'pip',
                'install',
                '-U',
                update_path,
            ],
        )


def apply_update(update_path: Path) -> Version:
    install_dependencies(update_path)
    with open(update_path / 'pyproject.toml', 'r') as src:
        pyproject = tomllib.loads(src.read())
    version = pyproject['project']['version']
    update_path.rename(update_path.parent / version)

    current = update_path.parent / 'current'

    current.unlink(missing_ok=True)
    os.symlink(update_path.parent / version, current, target_is_directory=True)
    return Version(version)


def apply_update(update_path: Path) -> Version:
    install_dependencies(update_path)

    with open(update_path / 'pyproject.toml', 'r') as src:
        pyproject = tomllib.loads(src.read())

    version = pyproject['project']['version']
    target_path = update_path.parent / version
    update_path.rename(target_path)

    current_link = update_path.parent / 'current'
    temp_link = current_link.with_name('current_tmp')
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
        exit(1)

    try:
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        os.replace(temp_link, current_link)
        logger.info('Current link successfully updated.')
    except Exception:
        logger.critical('Failed to replace current link.', exc_info=True)
        exit(1)

    return Version(version)
