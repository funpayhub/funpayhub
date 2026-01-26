from __future__ import annotations

import os
from typing import Any
from abc import ABC, abstractmethod
from asyncio import Lock
from pathlib import Path
from collections.abc import Sequence, Iterator, KeysView, ValuesView


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

    @property
    @abstractmethod
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
        self._source_id = f'file://{source}'

    def _count_products(self) -> int:
        count = 0
        with open(self._path, 'rb') as f:
            for line in f:
                if line.strip():
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
        self._sources: dict[str, GoodsSource] = {}

    def get(self, source_id: str) -> GoodsSource | None:
        return self._sources.get(source_id)

    async def add_source(
        self,
        source_cls: type[GoodsSource],
        source: Any,
        *args,
        **kwargs
    ) -> GoodsSource:
        source = source_cls(source, *args, **kwargs)
        if source.source_id in self._sources:
            raise ValueError(f'Source {source.source_id} already exists.')

        await source.load()
        self._sources[source.source_id] = source
        return source

    async def remove_source(self, source_id: str) -> None:
        if source_id not in self._sources:
            return

        source = self._sources[source_id]
        await source.remove()
        del self._sources[source_id]

    async def pop_goods(self, source_id: str, amount: int):
        source = self.get(source_id)
        if source is None:
            raise KeyError(f'Source {source_id} does not exist.')
        return await source.pop_goods(amount)

    async def get_goods(self, source_id: str, amount: int, start: int = 0):
        source = self.get(source_id)
        if source is None:
            raise KeyError(f'Source {source_id} does not exist.')
        return await source.get_goods(amount, start)

    def __len__(self) -> int:
        return len(self._sources)

    def __getitem__(self, key: str) -> GoodsSource:
        return self._sources[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._sources)

    def keys(self) -> KeysView[str]:
        return self._sources.keys()

    def values(self) -> ValuesView[GoodsSource]:
        return self._sources.values()