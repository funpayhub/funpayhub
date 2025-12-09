from __future__ import annotations


__all__ = ['HashinatorT1000']


import hashlib
import sqlite3
from pathlib import Path


class BadHashError(Exception):
    def __init__(self, hash: str) -> None:
        super().__init__()
        self.hash = hash

    def __str__(self) -> str:
        return f'Bad hash: {self.hash!r}'


class HashinatorStorage:
    def __init__(self, path: str | Path = 'storage/.hashes.db'):
        self._path = Path(path)
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()
        self.create_db()

    def create_db(self) -> None:
        with self.conn:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS "hashes" (
    "hash"	TEXT NOT NULL UNIQUE,
    "callback"	TEXT NOT NULL,
    "timestamp"	INTEGER NOT NULL,
    PRIMARY KEY("hash")
);""")
            self.cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_created_at ON hashes(timestamp);""",
            )

    def get_callback(self, hash: str, update_timestamp: bool = True) -> str | None:
        if update_timestamp:
            query = """
UPDATE hashes
SET timestamp = strftime('%s','now')
WHERE hash = ?
RETURNING callback
"""
        else:
            query = """SELECT callback FROM hashes WHERE hash = ?"""

        self.cursor.execute(query, (hash,))
        row = self.cursor.fetchone()

        return row[0] if row else None

    def update_timestamp(self, hash: str) -> None:
        self.cursor.execute(
            """UPDATE hashes SET timestamp = strftime('%s','now') WHERE hash = ?""",
            (hash,),
        )
        return

    def save_callbacks(self, hashes: dict[str, str]) -> None:
        self.cursor.executemany(
            """INSERT INTO hashes(hash, callback, timestamp)
VALUES (?, ?, strftime('%s','now'))
ON CONFLICT(hash) DO UPDATE SET
callback = excluded.callback,
timestamp = strftime('%s','now');""",
            ((hash, callback) for hash, callback in hashes.items()),
        )


class _HashinatorT1000:
    def __init__(self) -> None:
        self.hashes: dict[str, str] = {}
        self.storage = HashinatorStorage()

    def _md5(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def hash(self, text: str, save: bool = False) -> str:
        if len(text) <= 64:
            return text
        candidate = self._md5(text)

        with self.storage.conn:
            while True:
                callback = self.hashes.get(candidate)
                if not callback:
                    callback = self.storage.get_callback(candidate, update_timestamp=False)

                if not callback or callback == text:
                    self.hashes[candidate] = text
                    break
                candidate = self._md5(candidate)

            if save:
                self.storage.save_callbacks(self.hashes)
                self.hashes.clear()

            return f'<<{candidate}>>'

    def unhash(self, hash: str) -> str:
        if not self.is_hash(hash):
            raise BadHashError(hash)

        real_hash = hash[2:-2]
        result = self.hashes.get(real_hash, None) or self.storage.get_callback(real_hash)
        if result is None:
            raise BadHashError(hash)
        return result

    def save(self) -> None:
        if not self.hashes:
            return

        with self.storage.conn:
            self.storage.save_callbacks(self.hashes)
        self.hashes.clear()

    @classmethod
    def is_hash(self, value: str) -> bool:
        return value.startswith('<<') and value.endswith('>>') and len(value) == 36


HashinatorT1000 = _HashinatorT1000()
