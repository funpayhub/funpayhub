from __future__ import annotations


__all__ = ['FirstResponseCache']


import json
import time
from typing import Self
from types import MappingProxyType
from pathlib import Path


class FirstResponseCache:
    def __init__(self, path: Path | str) -> None:
        self._cache = {}
        self._path = Path(path)

    async def update(self, username: str, timestamp: int | None = None, save: bool = True) -> None:
        self._cache[username] = int(timestamp if timestamp is not None else time.time())
        if save:
            await self.save()

    async def get(self, username: str) -> int | None:
        return self._cache.get(username)

    async def is_new(self, username: str, delay: int = 3600 * 24) -> bool:
        ts = await self.get(username)
        if not ts:
            return True

        return (time.time() - ts) > delay

    async def remove(self, username: str, save: bool = True) -> int | None:
        result = self._cache.pop(username, None)
        if result is not None and save:
            await self.save()
        return result

    async def reset(self, save: bool = True) -> None:
        self._cache = {}
        if save:
            await self.save()

    async def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8') as f:
            f.write(json.dumps(self._cache, ensure_ascii=False))

    @property
    def path(self) -> Path:
        return self._path

    @property
    def cache(self) -> MappingProxyType[str, int]:
        return MappingProxyType(self._cache)

    @classmethod
    def from_file(cls, path: Path | str) -> Self:
        path = Path(path)

        if path.exists and not path.is_file():
            raise IsADirectoryError(f'{path} is not a file.')

        instance = cls(path)

        if not path.exists():
            return instance

        with path.open('r', encoding='utf-8') as f:
            instance._cache = json.load(f)

        return instance
