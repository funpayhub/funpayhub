from __future__ import annotations


from typing import Any, Self, TYPE_CHECKING


if TYPE_CHECKING:
    from .app import App
    from funpayhub.lib.translater import Translater
    from funpayhub.lib.properties import Properties
    from .telegram import TelegramApp
    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.hub.text_formatters import FormattersRegistry
    from funpayhub.lib.telegram.ui import UIRegistry
    from aiogram import Dispatcher, Bot


class WorkflowData:
    def __init__(self) -> None:
        super().__init__()
        self._locked = False

        self._data = {}

    def lock(self) -> None:
        self._locked = True

    def __getitem__(self, item: str) -> Any:
        if item in ['workflow_data', 'wfd']:
            return self
        return self._data[item]

    def __setitem__(self, key, value) -> None:
        with self:
            self._data[key] = value

    def __delitem__(self, key) -> None:
        with self:
            del self._data[key]

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

    @property
    def app(self) -> App:
        return self._data['hub']

    @property
    def properties(self) -> Properties:
        return self._data['properties']

    @property
    def translater(self) -> Translater:
        return self._data['translater']

    @property
    def telegram(self) -> TelegramApp:
        return self._data['tg']

    @property
    def tg_bot(self) -> Bot:
        return self._data['tg_bot']

    @property
    def tg_dispatcher(self) -> Dispatcher:
        return self._data['tg_dispatcher']

    @property
    def tg_ui_registry(self) -> UIRegistry:
        return self._data['tg_ui']

    @property
    def formatters_registry(self) -> FormattersRegistry:
        return self._data['fp_formatters']

    @property
    def goods_manager(self) -> GoodsSourcesManager:
        return self._data['goods_manager']
