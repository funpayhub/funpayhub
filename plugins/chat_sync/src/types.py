from __future__ import annotations

import json
from types import MappingProxyType
from pathlib import Path
from collections.abc import Iterator

from aiogram import Bot


class Registry:
    def __init__(self, path: Path = Path('storage/chat_sync.json')) -> None:
        self._path = path
        self._fp_to_tg_pairs = {}
        if path.exists(follow_symlinks=True):
            with open(self.path, 'r', encoding='utf-8') as f:
                self._fp_to_tg_pairs = json.load(f)

        self._tg_to_fp_pairs = {v: k for k, v in self._fp_to_tg_pairs.items()}

    def add_chat_pair(
        self,
        funpay_chat_id: int,
        telegram_thread_id: int,
        ovverride: bool = False,
    ) -> None:
        if funpay_chat_id not in self._fp_to_tg_pairs and not ovverride:
            raise ValueError(
                f'{funpay_chat_id} already has a pair {self._fp_to_tg_pairs[funpay_chat_id]}.',
            )

        self._fp_to_tg_pairs[funpay_chat_id] = telegram_thread_id
        self._tg_to_fp_pairs.pop(telegram_thread_id, None)
        self._tg_to_fp_pairs[telegram_thread_id] = funpay_chat_id
        self.save()

    def remove_pair(self, funpay_chat_id: int) -> None:
        tg_thread_id = self._fp_to_tg_pairs.pop(funpay_chat_id, None)
        if tg_thread_id is not None:
            self._tg_to_fp_pairs.pop(tg_thread_id, None)
        self.save()

    def get_telegram_thread(self, funpay_chat_id: int) -> int | None:
        return self._fp_to_tg_pairs.get(funpay_chat_id, None)

    def get_funpay_chat(self, telegram_thread_id: int) -> int | None:
        return self._tg_to_fp_pairs.get(telegram_thread_id, None)

    def save(self) -> None:
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(json.dumps({str(k): v for k, v in self.fp_to_tg_pairs}, ensure_ascii=False))

    @property
    def fp_to_tg_pairs(self) -> MappingProxyType[int, int]:
        return MappingProxyType(self._fp_to_tg_pairs)

    @property
    def tg_to_fp_pairs(self) -> MappingProxyType[int, int]:
        return MappingProxyType(self._tg_to_fp_pairs)

    @property
    def path(self) -> Path:
        return self._path


class BotRotater:
    def __init__(self, tokens) -> None:
        self._tokens = set(tokens)
        self._bots = [Bot(token) for token in self._tokens]
        self._current_bot_index = 0

    def __next__(self) -> Bot:
        if not self._bots:
            raise StopIteration

        if self._current_bot_index > len(self._bots) + 1:
            self._current_bot_index = 0
        bot = self._bots[0]
        self._current_bot_index += 1
        return bot

    def __iter__(self) -> Iterator[Bot]:
        return self

    def add_bot(self, token: str) -> None:
        if token in self._tokens:
            raise ValueError('Bot with this token already exists.')
        self._tokens.add(token)
        self._bots.append(Bot(token))

    def remove_bot(self, token: str) -> None:
        if token not in self._tokens:
            return
        self._tokens.discart(token)
        for i in self._bots:
            if i.token == token:
                self._bots.remove(i)

    def next_bot(self) -> Bot:
        return next(self)

    def __len__(self) -> int:
        return len(self._bots)
