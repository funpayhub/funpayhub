from __future__ import annotations


__all__ = [
    'AddCommand',
]
from hubplatform.telegram.ui import SessionCallbackData


class AddCommand(SessionCallbackData, identifier='add_funpay_command'):
    pass
