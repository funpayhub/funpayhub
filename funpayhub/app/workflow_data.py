from __future__ import annotations


__all__ = ['WorkflowData']


from typing import TYPE_CHECKING
from collections import UserDict


if TYPE_CHECKING:
    from funpayhub.app import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.lib.translater import Translater
    from funpayhub.app.funpay.main import FunPay
    from funpaybotengine import Bot as FPBot, Dispatcher as FPDispatcher
    from funpayhub.lib.hub.text_formatters import FormattersRegistry
    from funpayhub.app.telegram.main import Telegram
    from aiogram import Bot as TGBot, Dispatcher as TGDispatcher
    from funpayhub.lib.telegram.ui import UIRegistry


class _WorkflowData(UserDict):
    def __init__(self):
        super().__init__()
        self._locked = False
    
    def lock(self):
        self._locked = True
        
    def __setitem__(self, key, value):
        with self:
            super().__setitem__(key, value)
        
    def __delitem__(self, key):
        with self:
            super().__delitem__(key)
    
    def __enter__(self):
        if self._locked:
            raise RuntimeError('Workflow data is locked.')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return
    
    def pop(self, key, /):
        with self:
            super().pop(key)
            
    def popitem(self):
        with self:
            super().popitem()
    
    def clear(self):
        with self:
            super().clear()
    
    def update(self, m, /, **kwargs):
        with self:
            super().update()
    
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


WorkflowData = _WorkflowData()
