from __future__ import annotations


__all__ = [
    'ROUTERS',
    'MENUS',
    'MENU_MODS',
    'BUTTONS',
    'BUTTON_MODS',
]

from collections import defaultdict

from .menu import router as menu_router
from .goods import MENUS as GOODS_MENUS, MENUS_MODS as GOODS_MENU_MODS, router as goods_router
from .other import router as other_router
from .plugins import MENUS as PLUGIN_MENUS, router as plugins_router
from .updates import MENUS as UPDATE_MENUS, router as updates_router
from .autodelivery import (
    MENUS as AUTODELIVERY_MENUS,
    MENU_MODS as AUTODELIVERY_MENU_MODS,
    router as autodelivery_router,
)
from .autoresponse import MENU_MODS as AUTORESPONSE_MENU_MODS, router as autoresponse_router
from .help.handlers import router as help_router
from .funpay_actions import router as funpay_actions_router


ROUTERS = [
    menu_router,
    funpay_actions_router,
    updates_router,
    other_router,
    plugins_router,
    goods_router,
    autoresponse_router,
    autodelivery_router,
]

MENUS = [
    *UPDATE_MENUS,
    *PLUGIN_MENUS,
    *GOODS_MENUS,
    *AUTODELIVERY_MENUS,
]

BUTTONS = []


MENU_MODS = defaultdict(list)
_mods = [
    AUTORESPONSE_MENU_MODS,
    GOODS_MENU_MODS,
    AUTODELIVERY_MENU_MODS,
]

for mods_dict in _mods:
    for menu_id, mods in mods_dict.items():
        MENU_MODS[menu_id].extend(mods)


BUTTON_MODS = defaultdict(list)
_button_mods = []

for mods_dict in _button_mods:
    for button_id, mods in mods_dict.items():
        BUTTON_MODS[button_id].extend(mods)
