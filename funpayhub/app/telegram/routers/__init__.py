from __future__ import annotations

from .menu import router as menu_router
from .goods import router as goods_router
from .other import router as other_router
from .plugins import router as plugins_router
from .updates import router as updates_router
from .auto_delivery import router as auto_delivery_router
from .help.handlers import router as help_router
from .funpay_actions import router as funpay_actions_router


ROUTERS = [
    menu_router,
    funpay_actions_router,
    updates_router,
    other_router,
    plugins_router,
    goods_router,
    auto_delivery_router,
]
