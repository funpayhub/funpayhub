from __future__ import annotations

from funpayhub.lib.translater import _en


__all__ = [
    'NodesUIRegistry',
    'NodeMenuBuilder',
    'NodeButtonBuilder',
]


from typing import TYPE_CHECKING
from dataclasses import replace

from funpayhub.loggers import telegram_ui as logger

from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, ButtonBuilder

from .context import (
    NodeMenuContext as MenuCtx,
    NodeButtonContext as BtnCtx,
)


if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties as Props
    from funpayhub.lib.telegram.ui import UIRegistry as UI
    from funpayhub.lib.properties.base import Node


class _NodesUIRegistry:
    def __init__(self) -> None:
        self._buttons: dict[type[Node], str] = {}
        """Дефолтные фабрики кнопок параметров / категорий."""

        self._menus: dict[type[Node], str] = {}
        """Дефолтные фабрики меню просмотра параметров / категорий."""

    def get_button_builder(self, entry_type: type[Node]) -> str | None:
        if entry_type in self._buttons:
            return self._buttons[entry_type]
        for type, builder in self._buttons.items():
            if issubclass(entry_type, type):
                return builder
        return None

    def get_menu_builder(self, entry_type: type[Node]) -> str | None:
        if entry_type in self._menus:
            return self._menus[entry_type]
        for type, builder in self._menus.items():
            if issubclass(entry_type, type):
                return builder
        return None

    def add_button_builder(
        self,
        entry_type: type[Node],
        button_builder_id: str,
        overwrite: bool = False,
    ) -> None:
        if entry_type in self._buttons and not overwrite:
            raise KeyError(f'Button builder for entry of type {entry_type!r} already exists.')
        self._buttons[entry_type] = button_builder_id

        logger.info(
            _en('Button builder %s assigned as button builder for entries of type %s.'),
            button_builder_id,
            entry_type,
        )

    def add_menu_builder(
        self,
        entry_type: type[Node],
        menu_builder_id: str,
        overwrite: bool = False,
    ) -> None:
        if entry_type in self._menus and not overwrite:
            raise KeyError(f'Menu builder for entry of type {entry_type!r} already exists.')
        self._menus[entry_type] = menu_builder_id
        logger.info(
            _en('Menu builder %s assigned as menu builder for entries of type %r.'),
            menu_builder_id,
            entry_type,
        )


NodesUIRegistry = _NodesUIRegistry()


class NodeMenuBuilder(MenuBuilder, menu_id='node', context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, tg_ui: UI, properties: Props) -> Menu:
        entry = properties.get_node(ctx.entry_path)
        if (builder_id := NodesUIRegistry.get_menu_builder(type(entry))) is None:
            raise LookupError(f'Unknown entry type {type(entry)}.')
        context = replace(ctx, menu_id=builder_id)
        return await tg_ui.build_menu(context, finalize=False)


class NodeButtonBuilder(ButtonBuilder, button_id='node', context_type=BtnCtx):
    async def build(self, ctx: BtnCtx, tg_ui: UI, properties: Props) -> Button:
        entry = properties.get_node(ctx.entry_path)
        if (builder_id := NodesUIRegistry.get_button_builder(type(entry))) is None:
            raise LookupError(f'Unknown entry type {type(entry)}.')
        context = replace(ctx, button_id=builder_id)
        return await tg_ui.build_button(context)
