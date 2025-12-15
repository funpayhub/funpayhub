from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class SelectSetupLanguage(CallbackData, identifier='1'):
    lang: str
