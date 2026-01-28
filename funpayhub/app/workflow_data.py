from __future__ import annotations


__all__ = ['WorkflowData']


from typing import TYPE_CHECKING, Any
from collections import UserDict


if TYPE_CHECKING:
    from aiogram import Bot as TGBot, Dispatcher as TGDispatcher
    from funpaybotengine import Bot as FPBot, Dispatcher as FPDispatcher

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.lib.translater import Translater
    from funpayhub.app.funpay.main import FunPay
    from funpayhub.lib.telegram.ui import UIRegistry
    from funpayhub.app.telegram.main import Telegram
    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.hub.text_formatters import FormattersRegistry


class _WorkflowData(UserDict):
    def __init__(self) -> None:
        super().__init__()
        self._locked = False

    def lock(self) -> None:
        self._locked = True

    def __getitem__(self, item: str) -> Any:
        if item in ['workflow_data', 'wfd']:
            return self
        return super().__getitem__(item)

    def __setitem__(self, key, value) -> None:
        with self:
            super().__setitem__(key, value)

    def __delitem__(self, key) -> None:
        with self:
            super().__delitem__(key)

    def __enter__(self) -> _WorkflowData:
        if self._locked:
            raise RuntimeError('Workflow data is locked.')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return

    def pop(self, key, /) -> Any:
        with self:
            self.data.pop(key)

    def popitem(self) -> None:
        with self:
            self.data.popitem()

    def clear(self) -> None:
        with self:
            self.data.clear()

    def update(self, m, /, **kwargs) -> None:
        with self:
            self.data.update(m, **kwargs)

    @property
    def hub(self) -> FunPayHub:
        return self.data['hub']

    @property
    def properties(self) -> FunPayHubProperties:
        return self.data['properties']

    @property
    def translater(self) -> Translater:
        return self.data['translater']

    @property
    def funpay(self) -> FunPay:
        return self.data['fp']

    @property
    def fp_bot(self) -> FPBot:
        return self.data['fp_bot']

    @property
    def fp_dispatcher(self) -> FPDispatcher:
        return self.data['fp_dispatcher']

    @property
    def formatters_registry(self) -> FormattersRegistry:
        return self.data['fp_formatters']

    @property
    def telegram(self) -> Telegram:
        return self.data['tg']

    @property
    def tg_bot(self) -> TGBot:
        return self.data['tg_bot']

    @property
    def tg_dispatcher(self) -> TGDispatcher:
        return self.data['tg_dispatcher']

    @property
    def tg_ui_registry(self) -> UIRegistry:
        return self.data['tg_ui']

    @property
    def goods_manager(self) -> GoodsSourcesManager:
        return self.data['goods_manager']


WorkflowData = _WorkflowData()
