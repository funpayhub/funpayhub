from __future__ import annotations


__all__ = ['EXTENSION']

from hubplatform.app.components.telegram.component import TelegramComponentExtension

from .auto_delivery.ui import registry as auto_delivery_ui_registry
from .auto_delivery.router import router as auto_delivery_router


EXTENSION = TelegramComponentExtension(
    ui=[auto_delivery_ui_registry],
    routers=[auto_delivery_router],
)
