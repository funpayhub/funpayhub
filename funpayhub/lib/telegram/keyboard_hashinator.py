from __future__ import annotations


__all__ = ['HashinatorT1000']


import hashlib


class BadHashError(Exception):
    def __init__(self, hash: str) -> None:
        super().__init__()
        self.hash = hash

    def __str__(self) -> str:
        return f'Bad hash: {self.hash!r}'


class _HashinatorT1000:
    def __init__(self) -> None:
        self.hashes: dict[str, str] = {}

    def _sha1(self, text: str) -> str:
        return hashlib.sha1(text.encode('utf-8')).hexdigest()

    def hash(self, text: str) -> str:
        candidate = f'<<{self._sha1(text)}>>'
        while True:
            if candidate not in self.hashes:
                self.hashes[candidate] = text
                return candidate
            if self.hashes[candidate] == text:
                return candidate
            candidate = f'<<{self._sha1(candidate + ".")}>>'

    def unhash(self, hash: str) -> str | None:
        result = self.hashes.get(hash, None)
        if result is None:
            raise BadHashError(hash)
        return result

    @classmethod
    def is_hash(self, value: str) -> bool:
        return value.startswith('<<') and value.endswith('>>') and len(value) == 44


HashinatorT1000 = _HashinatorT1000()
