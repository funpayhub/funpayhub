from __future__ import annotations

from typing import Any, Self
from collections.abc import Callable, Iterator, MutableMapping


class WorkflowData(MutableMapping):
    def __init__(self) -> None:
        super().__init__()
        self._locked = False

        self._data: dict[str, Any] = {}
        self.check_items: dict[str, Callable[[Any], Any]] = {}

    def lock(self) -> None:
        self._locked = True

    def check_ready(self) -> None:
        for k, v in self.check_items.items():
            if k not in self._data:
                raise RuntimeError(f'Workflow data not ready: missing key {k!r}')

            try:
                v(self._data[k])
            except ValueError as e:
                raise RuntimeError(
                    f'Workflow data not ready: {k!r} didnt pass the check.',
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f'Workflow data not ready: an error occurred while checking {k!r}.',
                ) from e

    def __delitem__(self, item) -> None:
        with self:
            del self._data[item]

    def __getitem__(self, item: str) -> Any:
        if item in ['workflow_data', 'wfd']:
            return self
        return self._data[item]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __setitem__(self, key, value) -> None:
        with self:
            self._data[key] = value

    def __enter__(self) -> Self:
        if self._locked:
            raise RuntimeError('Workflow data locked.')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return

    def pop(self, key, /) -> Any:
        with self:
            self._data.pop(key)

    def popitem(self) -> None:
        with self:
            self._data.popitem()

    def clear(self) -> None:
        with self:
            self._data.clear()

    def update(self, m, /, **kwargs) -> None:
        with self:
            self._data.update(m, **kwargs)

    def __getattr__(self, item: str) -> Any:
        return self._data[item]
