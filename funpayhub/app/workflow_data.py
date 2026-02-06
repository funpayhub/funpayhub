from __future__ import annotations


__all__ = ['WorkflowData', 'get_wfd']


from typing import TYPE_CHECKING

from funpaybotengine import Bot as FPBot, Dispatcher as FPDispatcher

from funpayhub.lib.base_app import WorkflowData as BaseWorkflowData


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram


class WorkflowData(BaseWorkflowData):
    if TYPE_CHECKING:
        hub: FunPayHub
        properties: FunPayHubProperties
        telegram: Telegram
        fp: FunPay
        funpay: FunPay
        fp_bot: FPBot
        fp_dispatcher: FPDispatcher

    def __init__(self) -> None:
        super().__init__()

        from funpayhub.app.main import FunPayHub
        from funpayhub.app.properties import FunPayHubProperties
        from funpayhub.app.funpay.main import FunPay
        from funpayhub.app.telegram.main import Telegram

        self.check_items.update(
            {
                'app': lambda v: isinstance(v, FunPayHub),
                'tg': lambda v: isinstance(v, Telegram),
                'hub': lambda v: isinstance(v, FunPayHub),
                'fp': lambda v: isinstance(v, FunPay),
                'funpay': lambda v: isinstance(v, FunPay),
                'fp_bot': lambda v: isinstance(v, FPBot),
                'fp_dispatcher': lambda v: isinstance(v, FPDispatcher),
                'properties': lambda v: isinstance(v, FunPayHubProperties),
            },
        )


_WORKFLOW_DATA: WorkflowData | None = None


def get_wfd() -> WorkflowData:
    global _WORKFLOW_DATA
    if _WORKFLOW_DATA is None:
        _WORKFLOW_DATA = WorkflowData()

    return _WORKFLOW_DATA
