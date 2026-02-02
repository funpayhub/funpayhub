from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.lib.plugins import Plugin

from .types import Registry, BotRotater
from .properties import ChatSyncProperties
from .funpay.router import router as chat_sync_fp_router
from .telegram.router import router as chat_sync_tg_router


if TYPE_CHECKING:
    from funpaybotengine import Router as FPRouter
    from aiogram import Router as TGRouter


class ChatSyncPlugin(Plugin):
    _registry: Registry | None = None
    _rotater: BotRotater | None = None

    async def pre_setup(self) -> None:
        self._registry = Registry()
        self.hub.workflow_data['chat_sync_registry'] = self._registry

    async def properties(self) -> ChatSyncProperties:
        return ChatSyncProperties()

    async def funpay_routers(self) -> FPRouter:
        return chat_sync_fp_router

    async def telegram_routers(self) -> TGRouter:
        return chat_sync_tg_router

    async def post_setup(self) -> None:
        props: ChatSyncProperties = self.hub.properties.plugin_properties.get_properties(
            ['chat_sync'],
        )  # type: ignore
        self._rotater = BotRotater(tokens=props.bot_tokens.value)
        self.hub.workflow_data['chat_sync_rotater'] = self._rotater
