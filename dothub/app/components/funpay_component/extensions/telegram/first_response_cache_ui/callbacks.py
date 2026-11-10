from __future__ import annotations

from typing import Literal

from hubplatform.telegram.ui import SessionCallbackData


class SetChatTimestampToNow(SessionCallbackData, identifier='app.fp.frc.set_now'):
    chat_id: int


class RemoveChatFromCache(SessionCallbackData, identifier='app.fp.frc.remove'):
    chat_id: int


class StartChatInput(SessionCallbackData, identifier='app.fp.frc.start_input'):
    action: Literal['add', 'set_time']
    chat_id: int | None = None
