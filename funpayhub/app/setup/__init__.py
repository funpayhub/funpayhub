from __future__ import annotations

from . import tg, ui


TELEGRAM_SETUP_UI = [
    ui.SelectLanguageMenu,
    ui.SetupStepMenuBuilder,
]

TELEGRAM_SETUP_ROUTERS = [
    tg.router,
]
