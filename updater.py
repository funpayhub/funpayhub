import aiohttp
from aiohttp import ClientSession
from packaging.version import Version
from dataclasses import dataclass
import os
import zipfile
from pathlib import Path
import shutil


REPO = 'funpayhub/funpayhub'
CURRENT_VERSION = Version('0.1.2')
UPDATE_EXCLUDE = ['config', 'logs', 'plugins', 'storage']
RELEASES_PATH = Path(os.environ.get('RELEASES_PATH', 'releases'))
UPDATE_PATH = RELEASES_PATH / '.update'


@dataclass
class UpdateInfo:
    version: Version
    title: str
    description: str
    url: str


async def check_updates() -> UpdateInfo | None:
    async with ClientSession() as s:
        result = await s.get(
            f'https://api.github.com/repos/{REPO}/releases',
            headers={'Accept': 'application/vnd.github+json'}
        )
        data = await result.json()

    if not data:
        return None

    latest = data[0]
    latest_version = latest['tag_name'].replace('v', '').strip()
    if not latest_version:
        print('No new version available.')
        return None

    latest_version = Version(latest_version)
    return UpdateInfo(
        version=latest_version,
        title=latest['name'],
        description=latest['body'],
        url=latest['zipball_url']
    )



async def _download_update(url: str) -> None:
    async with ClientSession() as s:
        async with s.get(url) as response:
            response.raise_for_status()
            with open('.update.zip', 'wb') as f:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)


async def download_update(url: str) -> None:
    try:
        await _download_update(url)
    except aiohttp.ClientResponseError as e:
        print(e.status)
    except asyncio.TimeoutError:
        print('timeout')


def install_update(update_archive: str) -> None:
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


async def main():
    update = await check_updates()
    if not update:
        return

    await download_update(update.url)
    install_update('.update.zip')


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())