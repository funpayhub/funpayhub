from __future__ import annotations

from hubplatform.telegram.callback_data import CallbackData


class StopApp(CallbackData, identifier='app.main_menu.stop_app'):
    """Stops the app with ``exit_code``, which tells the launcher what to do next."""

    exit_code: int
