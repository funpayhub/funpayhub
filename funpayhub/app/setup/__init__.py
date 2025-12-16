from __future__ import annotations

from . import tg, ui


MENUS = [
    ui.SelectLanguageMenu,
    ui.EnterProxyMenu,
    ui.EnterUserAgentMenu,
]

TG_ROUTERS = [
    tg.router,
]
