from __future__ import annotations


__all__ = ['WorkflowData']


from typing import TYPE_CHECKING
from funpayhub.lib.base_app import WorkflowData as BaseWorkflowData


if TYPE_CHECKING:
    from funpaybotengine import Bot as FPBot, Dispatcher as FPDispatcher

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram


class _WorkflowData(BaseWorkflowData):
    if TYPE_CHECKING:
        properties: FunPayHubProperties
        telegram: Telegram

    def __init__(self) -> None:
        super().__init__()
        self._locked = False

    @property
    def hub(self) -> FunPayHub:
        return self._data['hub']

    @property
    def funpay(self) -> FunPay:
        return self._data['fp']

    @property
    def fp_bot(self) -> FPBot:
        return self._data['fp_bot']

    @property
    def fp_dispatcher(self) -> FPDispatcher:
        return self._data['fp_dispatcher']


WorkflowData = _WorkflowData()
