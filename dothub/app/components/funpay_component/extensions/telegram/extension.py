from __future__ import annotations


__all__ = ['EXTENSION']

from hubplatform.telegram.commands import Command
from hubplatform.app.components.telegram.component import TelegramComponentExtension

from dothub.app.components.telegram_component import TelegramComponent
from dothub.app.components.funpay_component.properties.telegram_notifications import (
    FunPayNotificationsCategory,
)

from .review_ui.ui import registry as review_ui_registry
from .component_ui.ui import registry as component_ui_registry
from .auto_delivery.ui import registry as auto_delivery_ui_registry
from .auto_response.ui import registry as commands_ui_registry
from .review_ui.router import router as review_ui_router
from .new_message_ui.ui import registry as new_message_ui_registry
from .component_ui.router import router as component_ui_router
from .offers_raiser_ui.ui import registry as offers_raiser_ui_registry
from .auto_delivery.router import router as auto_delivery_router
from .auto_response.router import router as commands_router
from .offers_raiser_ui.router import router as offers_raiser_router
from .first_response_cache_ui.ui import registry as first_response_cache_ui_registry
from .first_response_cache_ui.router import router as first_response_cache_router


async def _setup_call(component: TelegramComponent) -> None:
    component.properties.notifications.attach_node(FunPayNotificationsCategory())
    await component.properties.notifications.load()


EXTENSION = TelegramComponentExtension(
    ui=[
        auto_delivery_ui_registry,
        new_message_ui_registry,
        commands_ui_registry,
        review_ui_registry,
        first_response_cache_ui_registry,
        offers_raiser_ui_registry,
        component_ui_registry,
    ],
    commands=[
        Command(
            command='funpay_component',
            description='FunPay компонент',
        ),
        Command(
            command='first_response_cache',
            description='Кэш приветствий',
        ),
        Command(
            command='auto_raise_ui',
            description='Автоподнятие лотов',
        ),
    ],
    routers=[
        auto_delivery_router,
        commands_router,
        review_ui_router,
        first_response_cache_router,
        offers_raiser_router,
        component_ui_router,
    ],
    setup_call=_setup_call,
)
