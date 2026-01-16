from pathlib import Path
from types import MappingProxyType
import json


class Registry:
    def __init__(self, path: Path = Path('storage/chat_sync.json')):
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
        ovverride: bool = False
    ) -> None:
        if funpay_chat_id not in self._fp_to_tg_pairs and not ovverride:
            raise ValueError(f'{funpay_chat_id} already has a pair {self._fp_to_tg_pairs[funpay_chat_id]}.')

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

    def save(self):
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