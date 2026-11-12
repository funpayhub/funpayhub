from __future__ import annotations

from hubplatform.telegram.ui import SessionCallbackData
from hubplatform.telegram.callback_data import CallbackData


class CheckForUpdates(CallbackData, identifier='app.updates.check'):
    pass


class DownloadUpdate(SessionCallbackData, identifier='app.updates.download'):
    version: str
