from __future__ import annotations


__all__ = ['EXTENSION']

from hubplatform.app.components.telegram.component import TelegramComponentExtension

from dothub.app.components.telegram_component import TelegramComponent
from dothub.app.components.funpay_component.properties.telegram_notifications import (
    FunPayNotificationsCategory,
)

from .review_ui.ui import registry as review_ui_registry
from .auto_delivery.ui import registry as auto_delivery_ui_registry
from .auto_response.ui import registry as commands_ui_registry
from .new_message_ui.ui import registry as new_message_ui_registry
from .auto_delivery.router import router as auto_delivery_router
from .auto_response.router import router as commands_router


async def _setup_call(component: TelegramComponent) -> None:
    component.properties.notifications.attach_node(FunPayNotificationsCategory())
    await component.properties.notifications.load()


EXTENSION = TelegramComponentExtension(
    ui=[
        auto_delivery_ui_registry,
        new_message_ui_registry,
        commands_ui_registry,
        review_ui_registry,
    ],
    routers=[
        auto_delivery_router,
        commands_router,
    ],
    setup_call=_setup_call,
)
