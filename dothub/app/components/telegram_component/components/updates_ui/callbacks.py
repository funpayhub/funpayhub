from __future__ import annotations

from hubplatform.telegram.ui import SessionCallbackData
from hubplatform.telegram.callback_data import CallbackData


class CheckForUpdates(CallbackData, identifier='app.updates.check'):
    pass


class InstallUpdate(SessionCallbackData, identifier='app.updates.install'):
    version: str


class ApplyUpdate(SessionCallbackData, identifier='app.updates.apply'):
    version: str
