from __future__ import annotations


__all__ = ['UIRegistry']


from typing import Any, Protocol

from eventry.asyncio.callable_wrappers import CallableWrapper
from funpayhub.loggers import telegram_ui as logger

from .types import Menu, Button, MenuRenderContext
from .types import (
    MenuBuilderProto,
    MenuModFilterProto,
    MenuModProto,
    ButtonBuilderProto,
    ButtonModFilterProto,
    ButtonModProto,
    MenuBuilder,
    MenuModification,
    ButtonBuilder,
    ButtonModification,
)


class UIRegistry:
    def __init__(self, workflow_data: dict[str, Any] | None = None) -> None:
        self._menus: dict[str, MenuBuilder] = {}
        self._buttons: dict[str, ButtonBuilder] = {}  # todo

        self._workflow_data: dict[str, Any] = workflow_data if workflow_data is not None else {}

    def add_menu_builder(
        self,
        menu_id: str,
        builder: MenuBuilderProto,
        overwrite: bool = False
    ) -> None:
        mods = {}
        if menu_id in self._menus:
            if overwrite:
                raise KeyError(f'Menu {menu_id!r} already exists.')
            mods = self._menus[menu_id].modifications

        self._menus[menu_id] = MenuBuilder(CallableWrapper(builder), mods)

    def add_menu_modification(
        self,
        menu_id: str,
        modification_id: str,
        modification: MenuModProto,
        filter: MenuModFilterProto | None = None,
    ) -> None:
        if menu_id not in self._menus:
            raise KeyError(f'Menu {menu_id!r} does not exist.')
        if modification_id in self._menus[menu_id].modifications:
            raise KeyError(f'Menu {menu_id!r} already has a modification {modification_id!r}.')

        modification = MenuModification(
            modification_id,
            CallableWrapper(modification),
            CallableWrapper(filter) if filter is not None else None
        )
        self._menus[menu_id].modifications[modification_id] = modification

    def get_menu_builder(self, menu_id: str) -> MenuBuilder:
        return self._menus[menu_id]

    async def build_menu(self, context: MenuRenderContext, data: dict[str, Any]) -> Menu:
        try:
            builder = self.get_menu_builder(context.menu_id)
        except KeyError:
            logger.error(f'Menu {context.menu_id!r} not found.')
            raise

        logger.info(f'Building menu {context.menu_id!r}.')

        data = self._workflow_data | data
        data['data'] = data

        return await builder.build(self, context, data)
