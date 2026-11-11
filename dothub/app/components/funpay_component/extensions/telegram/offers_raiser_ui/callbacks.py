from __future__ import annotations

from hubplatform.telegram.ui import SessionCallbackData
from hubplatform.telegram.callback_data import CallbackData


class UpdateProfile(SessionCallbackData, identifier='app.fp.raiser.update_profile'):
    pass


class RerenderMenu(SessionCallbackData, identifier='app.fp.raiser.rerender'):
    pass

