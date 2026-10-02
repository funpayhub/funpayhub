from __future__ import annotations


__all__ = ['EXTENSION']

from hubplatform.app.components.telegram.component import TelegramComponentExtension

from funpayhub.app.components.telegram import TelegramComponent
from funpayhub.app.components.funpay.properties.telegram_notifications import (
    FunPayNotificationsCategory,
)

from .auto_delivery.ui import registry as auto_delivery_ui_registry
from .auto_delivery.router import router as auto_delivery_router


async def _setup_call(component: TelegramComponent) -> None:
    component.properties.notifications.attach_node(FunPayNotificationsCategory())
    await component.properties.notifications.load()


EXTENSION = TelegramComponentExtension(
    ui=[auto_delivery_ui_registry],
    routers=[auto_delivery_router],
    setup_call=_setup_call,
)
