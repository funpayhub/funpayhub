from __future__ import annotations

import os
from typing import Any
from abc import ABC, abstractmethod
from asyncio import Lock
from pathlib import Path
from collections.abc import Iterator, KeysView, Sequence, ValuesView

from funpayhub.lib.exceptions import NotEnoughGoodsError


class GoodsSource(ABC):
    @abstractmethod
    def __init__(self, source: Any, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    async def load(self) -> None: ...

    @abstractmethod
    async def reload(self) -> None: ...

    @abstractmethod
    async def add_goods(self, products: Sequence[str]) -> None: ...

    @abstractmethod
    async def pop_goods(self, amount: int) -> list[str]: ...

    @abstractmethod
    async def get_goods(self, amount: int, start: int = 0) -> list[str]: ...

    @abstractmethod
    async def set_goods(self, goods: list[str]) -> None: ...

    @abstractmethod
    async def remove_goods(self, from_index: int, amount: int) -> None: ...

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

    @property
    def display_source(self) -> str:
        return self.source_id

    @property
    def display_source_type(self) -> str:
        return self.__class__.__name__


class FileGoodsSource(GoodsSource):
    """
    Представляет файл с товарами.
    """

    def __init__(self, source: str | Path) -> None:
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
                if line.rstrip(b'\r\n'):
                    count += 1
        return count

    def _create_file(self) -> None:
        if not self.path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.touch()
            self._goods_amount = 0

    async def load(self) -> None:
        if not os.path.exists(self._path):
            self._create_file()
        else:
            self._goods_amount = self._count_products()

    async def reload(self) -> None:
        async with self._lock:
            await self.load()

    async def unload(self) -> None:
        return

    async def remove(self) -> None:
        async with self._lock:
            if self.path.exists():
                os.remove(self.path)

    async def add_goods(self, products: Sequence[str]) -> None:
        if not len(products):
            return

        async with self._lock:
            self._create_file()
            added_products = 0
            with open(self._path, 'a', encoding='utf-8') as f:
                # На случай, если пользователь своими ручонками сам засуну товарный файл без
                # пустой строки в конце.
                # Все методы получения / удаления товаров и т.д., корректно обрабатывают
                # пустые строки.
                f.write('\n')
                for i in products:
                    i = i.rstrip('\r\n')
                    if not i:
                        continue
                    f.write(i + '\n')
                    added_products += 1
            self._goods_amount += added_products

    async def pop_goods(self, amount: int) -> list[str]:
        if amount < 1:
            raise ValueError('Amount must be greater than 0.')

        async with self._lock:
            self._create_file()
            tmp = self._path.with_suffix('.tmp')
            result: list[str] = []
            new_amount = 0
            current_index = 0

            with (
                self._path.open('r', encoding='utf-8') as fin,
                tmp.open('w', encoding='utf-8') as fout,
            ):
                for line in fin:
                    line = line.rstrip('\r\n')
                    if not line:
                        continue

                    if current_index < amount:
                        result.append(line)
                    else:
                        fout.write(line + '\n')
                        new_amount += 1

                    current_index += 1

            if len(result) < amount:
                tmp.unlink(missing_ok=True)
                self._goods_amount = current_index
                raise NotEnoughGoodsError(self)

            tmp.replace(self._path)
            self._goods_amount = new_amount
            return result

    async def get_goods(self, amount: int, start: int = 0) -> list[str]:
        if start < 0 or amount < -1:
            raise ValueError('Start must be greater than 0.')

        if amount == -1:
            amount = float('inf')  # type: ignore[assignment]

        if start > self._goods_amount:
            return []

        result: list[str] = []
        async with self._lock:
            with open(self.path, 'r', encoding='utf-8') as f:
                current_line = 0
                while current_line < start:
                    try:
                        line = next(f).rstrip('\r\n')
                        if not line:
                            continue
                        current_line += 1
                    except StopIteration:
                        break

                while len(result) < amount:
                    try:
                        line = next(f).rstrip('\r\n')
                        if not line:
                            continue
                        result.append(line)
                    except StopIteration:
                        break
        return result

    async def set_goods(self, goods: list[str]) -> None:
        async with self._lock:
            self._create_file()
            tmp = self._path.with_suffix('.tmp')
            amount = 0

            with tmp.open('w', encoding='utf-8') as f:
                for i in goods:
                    i = i.rstrip('\r\n')
                    if not i:
                        continue
                    f.write(i + '\n')
                    amount += 1

            tmp.replace(self._path)
            self._goods_amount = amount

    async def remove_goods(self, from_index: int, amount: int) -> None:
        if amount < 1:
            raise ValueError('Amount must be greater than 0.')

        async with self._lock:
            tmp = self._path.with_suffix('.tmp')
            to_index = from_index + amount
            new_amount = 0
            current_product_index = 0
            with (
                self._path.open('r', encoding='utf-8') as fin,
                tmp.open('w', encoding='utf-8') as fout,
            ):
                for line in fin:
                    if not line.rstrip('\r\n'):
                        continue
                    if not (from_index <= current_product_index < to_index):
                        fout.write(line)
                        new_amount += 1
                    current_product_index += 1

            tmp.replace(self._path)
            self._goods_amount = new_amount

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

    @property
    def display_source(self) -> str:
        return str(self._path.absolute())

    @property
    def display_source_type(self) -> str:
        return '$txt_source_type'


class GoodsSourcesManager:
    def __init__(self) -> None:
        self._sources: dict[str, GoodsSource] = {}
        self._lock = Lock()

    def get(self, source_id: str) -> GoodsSource | None:
        return self._sources.get(source_id)

    async def add_source[S: GoodsSource](
        self,
        source_cls: type[S],
        source: Any,
        *args: Any,
        **kwargs: Any,
    ) -> S:
        async with self._lock:
            source = source_cls(source, *args, **kwargs)
            if source.source_id in self._sources:
                raise ValueError(f'Source {source.source_id} already exists.')

            await source.load()
            self._sources[source.source_id] = source
            return source

    async def remove_source(self, source_id: str) -> None:
        async with self._lock:
            if source_id not in self._sources:
                return

            source = self._sources[source_id]
            await source.remove()
            del self._sources[source_id]

    async def pop_goods(self, source_id: str, amount: int) -> list[str]:
        source = self.get(source_id)
        if source is None:
            raise KeyError(f'Source {source_id} does not exist.')
        return await source.pop_goods(amount)

    async def get_goods(self, source_id: str, amount: int, start: int = 0) -> list[str]:
        source = self.get(source_id)
        if source is None:
            raise KeyError(f'Source {source_id} does not exist.')
        return await source.get_goods(amount, start)

    async def add_goods(self, source_id: str, goods: list[str]) -> list[str]:
        async with self._lock:
            source = self.get(source_id)
            if source is None:
                raise KeyError(f'Source {source_id} does not exist.')
            await source.add_goods(goods)

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
