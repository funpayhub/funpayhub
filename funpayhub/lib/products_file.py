from __future__ import annotations

import os
from typing import Any
from abc import ABC, abstractmethod
from asyncio import Lock
from pathlib import Path
from collections.abc import Sequence


class NotEnoughProductsError(RuntimeError):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class GoodsSource(ABC):
    @abstractmethod
    def __init__(self, source: Any, *args, **kwargs) -> None: ...

    @abstractmethod
    async def load(self) -> None: ...

    @abstractmethod
    async def add_goods(self, products: Sequence[str]) -> None: ...

    @abstractmethod
    async def pop_goods(self, amount: int) -> list[str]: ...

    @abstractmethod
    async def get_goods(self, amount: int, start: int = 0) -> list[str]: ...

    @abstractmethod
    async def unload(self) -> None: ...

    @abstractmethod
    async def remove(self) -> None: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    @property
    def source_id(self) -> str: ...

    @property
    def display_id(self) -> str:
        return self.source_id


class FileGoodsSource(GoodsSource):
    """
    Представляет файл с товарами.
    """

    def __init__(self, source: str | Path):
        if not isinstance(source, (str, Path)):
            raise ValueError('Source must be a string or Path object.')

        self._path = Path(source) if isinstance(source, str) else source
        self._goods_amount = 0
        self._lock = Lock()
        self._source_id = f'File - {source}'

    def _count_products(self) -> int:
        count = 0
        with open(self._path, 'rb') as f:
            for _ in f:
                count += 1
        return count

    def _create_file(self):
        if not self.path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.touch()
            self._goods_amount = 0

    async def load(self) -> None:
        if not os.path.exists(self._path):
            self._create_file()
        else:
            self._goods_amount = self._count_products()

    async def unload(self) -> None:
        return

    async def remove(self) -> None:
        async with self._lock:
            if self.path.exists():
                os.remove(self.path)

    async def add_goods(self, products: Sequence[str]) -> None:
        async with self._lock:
            self._create_file()
            with open(self._path, 'a', encoding='utf-8') as f:
                f.write('\n' + '\n'.join(products))
            self._goods_amount += len(products)

    async def pop_goods(self, amount: int) -> list[str]:
        async with self._lock:
            self._create_file()

            if amount > len(self):
                raise NotEnoughProductsError()

            with open(self.path, 'r', encoding='utf-8') as f:
                products = f.read().splitlines()

            result = products[:amount]
            if len(products) < amount:
                self._goods_amount = len(products)
                raise NotEnoughProductsError()

            with open(self.path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(products[amount:]))

            self._goods_amount -= amount
            return result

    async def get_goods(self, amount: int, start: int = 0) -> list[str]:
        if start < 0 or amount < 0:
            raise ValueError('Start must be greater than 0.')

        if start > self._goods_amount:
            return []

        result = []
        async with self._lock:
            with open(self.path, 'r', encoding='utf-8') as f:
                current_line = 0
                while current_line < start:
                    next(f)
                for i in range(amount):
                    try:
                        result.append(next(f))
                    except StopIteration:
                        break
        return result

    def __len__(self) -> int:
        return self._goods_amount

    @property
    def path(self) -> Path:
        return self._path

    @property
    def source_id(self) -> str:
        return self._source_id

    @property
    def display_id(self) -> str:
        return self._path.name


class GoodsSourcesManager:
    def __init__(self):
        self._sources = {}

    def get(self, source_id: str) -> GoodsSource | None:
        return self._sources.get(source_id)

    def add_source(self, source: GoodsSource): ...

    def remove_source(self, source_id: str) -> None: ...

    async def get_goods(self, source_id: str, amount: int):
        source = self.get(source_id)
        return await source.pop_goods(amount)
