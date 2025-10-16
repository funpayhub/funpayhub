from __future__ import annotations


__all__ = ['UIRegistry']


from typing import Any, Type, Concatenate, Protocol
from collections.abc import Callable, Awaitable

from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.translater import Translater
from funpayhub.loggers import telegram_ui as logger

from .types import Menu, Button, UIRenderContext


class MenuBuilderProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: UIRenderContext,
        *__args: Any,
        **__kwargs: Any
    ) -> Menu: ...


class UIRegistry:
    def __init__(self, workflow_data: dict[str, Any] | None = None) -> None:
        self._menus: dict[str, CallableWrapper[Menu]] = {}
        self._modifications: dict[str, list[CallableWrapper[Menu]]] = {}

        self._workflow_data: dict[str, Any] = workflow_data if workflow_data is not None else {}

    def add_menu_builder(
        self,
        menu_id: str,
        builder: MenuBuilderProto,
        overwrite: bool = False
    ) -> None:
        if menu_id in self._menus and not overwrite:
            raise KeyError(f'Menu {menu_id!r} already exists.')
        self._menus[menu_id] = CallableWrapper(builder)

