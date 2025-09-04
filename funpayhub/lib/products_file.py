from pathlib import Path
from collections.abc import Sequence
from typing import Any
from asyncio import Lock
import os


class NotEnoughProductsError(RuntimeError):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class ProductsFile:
    def __init__(
        self,
        path: str | Path
    ):
        self._path = Path(path) if isinstance(path, str) else path

        if not os.path.exists(self._path):
            self._create_products_file()
        else:
            self._products_amount = self._count_products()

        self._lock = Lock()

    def _count_products(self) -> int:
        count = 0
        with open(self._path, 'rb') as f:
            for block in iter(lambda: f.read(65536), b""):
                count += block.count(b"\n")
        return count

    async def add_products(self, products: Sequence[str]) -> None:
        self._create_products_file()
        async with self._lock:
            with open(self._path, 'w', encoding='utf-8') as f:
                f.write('\n' + '\n'.join(products))
            self._products_amount += len(products)

    async def get_products(self, amount: int) -> list[str]:
        # todo: make reading from the end of the file + truncating

        async with self._lock:
            if amount > self.products_amount:
                raise NotEnoughProductsError()

            with open(self.path, 'r', encoding='utf-8') as f:
                products = f.read().splitlines()

            result = products[:amount]

            with open(self.path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(products[amount:]))

            self._products_amount -= amount
            return result

    def _create_products_file(self):
        if not self.path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.touch()
            self._products_amount = 0

    @property
    def products_amount(self) -> int:
        return self._products_amount

    @property
    def path(self) -> Path:
        return self._path


class ProductsFileManager:
    ...
