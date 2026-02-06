from __future__ import annotations


__all__ = [
    'ROUTERS',
    'MENUS',
    'MENU_MODS',
    'BUTTONS',
    'BUTTON_MODS',
]

from .menu import router as menu_router
from .goods import router as goods_router
from .other import router as other_router
from .plugins import router as plugins_router
from .updates import router as updates_router
from .auto_delivery import router as auto_delivery_router
from .help.handlers import router as help_router
from .funpay_actions import router as funpay_actions_router
from .autoresponse import router as autoresponse_router, MENU_MODS as AUTORESPONSE_MENU_MODS
from collections import defaultdict


ROUTERS = [
    menu_router,
    funpay_actions_router,
    updates_router,
    other_router,
    plugins_router,
    goods_router,
    autoresponse_router,
    auto_delivery_router,
]

MENUS = []
BUTTONS = []


MENU_MODS = defaultdict(list)
_mods = [AUTORESPONSE_MENU_MODS]

for mods_dict in _mods:
    for menu_id, mods in mods_dict.items():
        MENU_MODS[menu_id].extend(mods)


BUTTON_MODS = defaultdict(list)
_button_mods = []

for mods_dict in _button_mods:
    for button_id, mods in mods_dict.items():
        BUTTON_MODS[button_id].extend(mods)