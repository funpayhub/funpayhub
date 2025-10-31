from .funpay_actions import router as funpay_actions_router
from .help.handlers import router as help_router
from .menu import router as menu_router

ROUTERS = [
    menu_router,
    funpay_actions_router
]
