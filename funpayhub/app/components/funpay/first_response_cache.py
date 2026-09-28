from __future__ import annotations


__all__ = ['FirstResponseCache']


import json
import time
from typing import Self
from types import MappingProxyType
from pathlib import Path


class FirstResponseCache:
    def __init__(self, path: Path | str) -> None:
        self._cache: dict[str, int] = {}
        self._path = Path(path)

    def update(self, *chat_ids: int | str, ts: int | None = None, save: bool = True) -> None:
        for i in chat_ids:
            self._cache[str(i)] = int(ts if ts is not None else time.time())
        if save:
            self.save()

    def get(self, chat_id: int | str) -> int | None:
        return self._cache.get(str(chat_id))

    def get_timed_out(self, *chat_ids: int | str, delay: int = 3600 * 24) -> set[int | str]:
        return {i for i in chat_ids if self.is_new(i, delay)}

    def is_new(self, chat_id: int | str, delay: int = 3600 * 24) -> bool:
        ts = self.get(chat_id)
        if not ts:
            return True

        return (time.time() - ts) > delay

    def remove(self, chat_id: int | str, save: bool = True) -> int | None:
        result = self._cache.pop(str(chat_id), None)
        if result is not None and save:
            self.save()
        return result

    def reset(self, save: bool = True) -> None:
        self._cache = {}
        if save:
            self.save()

    def save(self) -> None:
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

        if path.exists() and not path.is_file():
            raise IsADirectoryError(f'{path} is not a file.')

        instance = cls(path)

        if not path.exists():
            return instance

        with path.open('r', encoding='utf-8') as f:
            instance._cache = json.load(f)

        return instance
