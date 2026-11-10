from __future__ import annotations


__all__ = ['FirstResponseCache']


import time
from typing import Self
from pathlib import Path

import aiosqlite


class FirstResponseCache:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._db: aiosqlite.Connection | None = None

    @property
    def path(self) -> Path:
        return self._path

    async def get(self, chat_id: int) -> int:
        async with self._conn.execute(
            'SELECT ts FROM first_response WHERE chat_id = ?',
            (chat_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else -1

    async def get_all(self) -> dict[int, int]:
        """Returns all stored chats as ``{chat_id: timestamp}``, most recent first."""
        async with self._conn.execute(
            'SELECT chat_id, ts FROM first_response ORDER BY ts DESC',
        ) as cursor:
            return {row[0]: row[1] for row in await cursor.fetchall()}

    async def get_new(self, *chat_ids: int, max_age: int = 3600 * 24) -> tuple[int, ...]:
        threshold = time.time() - max_age

        if not chat_ids:
            async with self._conn.execute(
                'SELECT chat_id FROM first_response WHERE ts < ?',
                (threshold,),
            ) as cursor:
                return tuple(row[0] for row in await cursor.fetchall())

        # Chats that are not stored count as timed out, so look up the fresh ones instead.
        placeholders = ', '.join('?' * len(chat_ids))
        async with self._conn.execute(
            f'SELECT chat_id FROM first_response WHERE ts >= ? AND chat_id IN ({placeholders})',
            (threshold, *chat_ids),
        ) as cursor:
            fresh = {row[0] for row in await cursor.fetchall()}
        return tuple(i for i in chat_ids if i not in fresh)

    async def is_new(self, chat_id: int, max_age: int = 3600 * 24) -> bool:
        return await self.get(chat_id) < time.time() - max_age

    async def update(self, *chat_ids: int, ts: int | None = None) -> None:
        ts = int(ts if ts is not None else time.time())
        await self._conn.executemany(
            'INSERT OR REPLACE INTO first_response (chat_id, ts) VALUES (?, ?)',
            [(i, ts) for i in chat_ids],
        )
        await self._conn.commit()

    async def remove(self, *chat_ids: int) -> None:
        await self._conn.executemany(
            'DELETE FROM first_response WHERE chat_id = ?',
            [(i,) for i in chat_ids],
        )
        await self._conn.commit()

    async def load(self) -> None:
        """Opens the database and creates the table if it does not exist."""
        if self._db is None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(self._path)
        await self._db.execute(
            'CREATE TABLE IF NOT EXISTS first_response ('
            'chat_id INTEGER PRIMARY KEY, ts INTEGER NOT NULL)',
        )
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @classmethod
    async def from_db(cls, path: Path | str) -> Self:
        instance = cls(path)
        await instance.load()
        return instance

    @property
    def _conn(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError('Database is not loaded. Call .load() first.')
        return self._db
