from __future__ import annotations


__all__ = ['EXTENSION']

from hubplatform.app.components.telegram.component import TelegramComponentExtension

from .auto_delivery.ui import registry as auto_delivery_ui_registry


EXTENSION = TelegramComponentExtension(
    ui=[auto_delivery_ui_registry],
)
