import aiohttp
from aiohttp import ClientSession
from packaging.version import Version
from dataclasses import dataclass
import os


REPO = 'funpayhub/funpayhub'
CURRENT_VERSION = Version('0.1.2')
UPDATE_EXCLUDE = ['config', 'logs', 'plugins', 'storage']


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

    latest = data[-1]
    latest_version = latest['tag_name'].replace('v', '').strip()
    if not latest_version:
        return None

    latest_version = Version(latest_version)
    return UpdateInfo(
        version=latest_version,
        title=data['name'],
        description=data['body'],
        url=data['zipball_url']
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


def install_update(update_path: str) -> None:
    # Скопировать старые файлы в 'fph.backup'
    # Распаковать новые файлы
    # Удалить ненужные файлы
    # Установить зависимости
    # Удалить backup
    # перезапуститься
    ...


if __name__ == '__main__':
    import asyncio
    asyncio.run(check_updates())