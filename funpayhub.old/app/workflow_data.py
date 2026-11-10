from __future__ import annotations


__all__ = ['WorkflowData', 'get_wfd']


from typing import TYPE_CHECKING

from funpaybotengine import (
    Bot as FPBot,
    Dispatcher as FPDispatcher,
)
from dothub.lib.base_app import WorkflowData as BaseWorkflowData


if TYPE_CHECKING:
    from dothub.app.main import FunPayHub
    from dothub.app.plugin import PluginManager
    from dothub.app.funpay.main import FunPay
    from dothub.app.telegram.main import Telegram
    from dothub.app.first_response_cache import FirstResponseCache

    from dothub.app.properties import FunPayHubProperties


class WorkflowData(BaseWorkflowData):
    if TYPE_CHECKING:
        hub: FunPayHub
        properties: FunPayHubProperties
        telegram: Telegram
        fp: FunPay
        funpay: FunPay
        fp_bot: FPBot
        fp_dispatcher: FPDispatcher
        plugins_manager: PluginManager
        first_response_cache: FirstResponseCache

    def __init__(self) -> None:
        super().__init__()

        from dothub.app.main import FunPayHub
        from dothub.app.plugin import PluginManager
        from dothub.app.funpay.main import FunPay
        from dothub.app.telegram.main import Telegram
        from dothub.app.first_response_cache import FirstResponseCache

        from dothub.app.properties import FunPayHubProperties

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
                'plugins_manager': lambda v: isinstance(v, PluginManager),
                'first_response_cache': lambda v: isinstance(v, FirstResponseCache),
            },
        )


_WORKFLOW_DATA: WorkflowData | None = None


def get_wfd() -> WorkflowData:
    global _WORKFLOW_DATA
    if _WORKFLOW_DATA is None:
        _WORKFLOW_DATA = WorkflowData()

    return _WORKFLOW_DATA
