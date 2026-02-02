from __future__ import annotations

import json
from types import MappingProxyType
from pathlib import Path
from collections.abc import Iterator

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


class Registry:
    """
    Реестр пар FunPay Chat ID - Telegram Thread ID.

    :param path: Путь до файла сохранения реестра.
    """

    def __init__(self, path: Path = Path('storage/chat_sync/chat_sync.json')) -> None:
        self._path = path
        self._fp_to_tg_pairs = {}
        if path.exists(follow_symlinks=True):
            with open(self.path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    self._fp_to_tg_pairs = {int(k): v for k, v in data.items()}
                except Exception as e:
                    # todo: logging
                    self._fp_to_tg_pairs = {}

        self._tg_to_fp_pairs = {v: k for k, v in self._fp_to_tg_pairs.items()}

    def add_chat_pair(
        self,
        funpay_chat_id: int,
        telegram_thread_id: int,
        override: bool = False,
    ) -> None:
        """
        Добавляет связку чатов.

        :param funpay_chat_id: ID чата FunPay.
        :param telegram_thread_id: ID телеграм темы.
        :param override: Перезаписать ли существующее значение? Если `False` и телеграм тема уже
            назначена для переданного FunPay chat id - возбуждает исключение `ValueError`.
        """
        if funpay_chat_id in self._fp_to_tg_pairs and not override:
            raise ValueError(
                f'{funpay_chat_id} already has a pair {self._fp_to_tg_pairs[funpay_chat_id]}.',
            )

        self._fp_to_tg_pairs[funpay_chat_id] = telegram_thread_id
        self._tg_to_fp_pairs[telegram_thread_id] = funpay_chat_id
        self.save()

    def remove_pair(self, funpay_chat_id: int) -> None:
        """
        Удаляет связку чатов.

        :param funpay_chat_id: ID чата FunPay.
        """
        tg_thread_id = self._fp_to_tg_pairs.pop(funpay_chat_id, None)
        if tg_thread_id is not None:
            self._tg_to_fp_pairs.pop(tg_thread_id, None)
        self.save()

    def get_telegram_thread(self, funpay_chat_id: int) -> int | None:
        """
        Возвращает привязанный к FunPay чату ID Telegram темы.

        :param funpay_chat_id: ID FunPay чата.

        :return: ID привязанной Telegram темы или `None`.
        """
        return self._fp_to_tg_pairs.get(funpay_chat_id, None)

    def get_funpay_chat(self, telegram_thread_id: int) -> int | None:
        """
        Возвращает привязанный к Telegram теме ID FunPay чата.

        :param telegram_thread_id: ID Telegram темы.

        :return: ID привязанного FunPay чата или `None`.
        """
        return self._tg_to_fp_pairs.get(telegram_thread_id, None)

    def save(self) -> None:
        """
        Сохраняет все связки в указанный при инициализации реестра путь в формате JSON.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(
                json.dumps(
                    {str(k): v for k, v in self.fp_to_tg_pairs.items()}, ensure_ascii=False
                )
            )

    @property
    def fp_to_tg_pairs(self) -> MappingProxyType[int, int]:
        """
        Неизменяемый словарь (`MappingProxyType`) пар {ID чата FunPay: ID Telegram темы}.
        """
        return MappingProxyType(self._fp_to_tg_pairs)

    @property
    def tg_to_fp_pairs(self) -> MappingProxyType[int, int]:
        """
        Неизменяемый словарь (`MappingProxyType`) пар {ID Telegram темы: ID чата FunPay}.
        """
        return MappingProxyType(self._tg_to_fp_pairs)

    @property
    def path(self) -> Path:
        """
        Путь сохранения реестра.
        """
        return self._path


class BotRotater:
    """
    Циклический итератор Telegram ботов.

    Хранит набор ботов и поочерёдно возвращает их по кругу (round-robin).
    Поддерживает добавление и удаление ботов во время работы.
    """
    _DEFAULT_BOT_PROPERTIES = DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        allow_sending_without_reply=True,
        link_preview_is_disabled=True
    )

    def __init__(self, tokens) -> None:
        self._tokens = set(tokens)
        self._bots = [self._bot_from_token(token) for token in self._tokens]
        self._current_bot_index = 0

    def __next__(self) -> Bot:
        if not self._bots:
            raise StopIteration

        if self._current_bot_index > len(self._bots) - 1:
            self._current_bot_index = 0
        bot = self._bots[self._current_bot_index]
        self._current_bot_index += 1
        return bot

    def __iter__(self) -> Iterator[Bot]:
        return self

    def add_bot(self, token: str) -> None:
        if token in self._tokens:
            raise ValueError('Bot with this token already exists.')
        self._tokens.add(token)
        self._bots.append(self._bot_from_token(token))

    def remove_bot(self, token: str) -> None:
        if token not in self._tokens:
            return
        self._tokens.discard(token)
        for i in self._bots:
            if i.token == token:
                self._bots.remove(i)

    def next_bot(self) -> Bot:
        return next(self)

    def _bot_from_token(self, token: str) -> Bot:
        return Bot(token=token, default=self._DEFAULT_BOT_PROPERTIES)

    def __len__(self) -> int:
        return len(self._bots)
