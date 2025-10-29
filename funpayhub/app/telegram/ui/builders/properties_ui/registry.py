from __future__ import annotations


__all__ = ['EntriesUIRegistry']


from typing import Any, Type

from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.app.telegram.ui.ids import MenuIds, ButtonIds
from funpayhub.loggers import telegram_ui as logger
from funpayhub.lib.properties.base import Entry
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, ButtonBuilder
from funpayhub.app.telegram.ui.builders.properties_ui.context import (
    EntryMenuContext,
    EntryButtonContext,
)


class _EntriesUIRegistry:
    def __init__(self) -> None:
        self._buttons: dict[type[Entry], CallableWrapper[Button]] = {}
        """Дефолтные фабрики кнопок параметров / категорий."""

        self._menus: dict[type[Entry], CallableWrapper[Menu]] = {}
        """Дефолтные фабрики меню просмотра параметров / категорий."""

    def get_button_builder(self, entry_type: Type[Entry]) -> CallableWrapper[Button] | None:
        if entry_type in self._buttons:
            return self._buttons[entry_type]
        for type, builder in self._buttons.items():
            if issubclass(entry_type, type):
                return builder
        return None

    def get_menu_builder(self, entry_type: Type[Entry]) -> CallableWrapper[Menu] | None:
        if entry_type in self._menus:
            return self._menus[entry_type]
        for type, builder in self._menus.items():
            if issubclass(entry_type, type):
                return builder
        return None

    def add_button_builder(
        self,
        entry_type: Type[Entry],
        builder: Any,  # todo: type
        overwrite: bool = False,
    ) -> None:
        if entry_type in self._buttons and not overwrite:
            raise KeyError(f'Properties button builder for {entry_type} already exists.')
        self._buttons[entry_type] = CallableWrapper(builder)
        logger.info(f'Entry button builder for {entry_type!r} added to entries ui registry.')

    def add_menu_builder(
        self,
        entry_type: Type[Entry],
        builder: Any,  # todo: type
        overwrite: bool = False,
    ) -> None:
        if entry_type in self._menus and not overwrite:
            raise KeyError(f'Entry menu builder for {entry_type!r} already exists.')
        self._menus[entry_type] = CallableWrapper(builder)
        logger.info(f'Entry menu builder for {entry_type!r} added to entries ui registry.')


EntriesUIRegistry = _EntriesUIRegistry()


class PropertiesEntryMenuBuilder(MenuBuilder):
    id = MenuIds.properties_entry
    context_type = EntryMenuContext

    async def build(self, ctx: EntryMenuContext, data: dict[str, Any]) -> Menu:
        logger.debug(f'Menu builder for {ctx.entry.path} ({type(ctx.entry)}) requested.')

        if (builder := EntriesUIRegistry.get_menu_builder(type(ctx.entry))) is None:
            raise LookupError(f'Unknown entry type {type(ctx.entry)}.')

        return await builder((ctx,), data=data)


class PropertiesEntryButtonBuilder(ButtonBuilder):
    id = ButtonIds.properties_entry
    context_type = EntryButtonContext

    async def build(self, ctx: EntryButtonContext, data: dict[str, Any]) -> Button:
        logger.debug(f'Button builder for {ctx.entry.path} ({type(ctx.entry)}) requested.')

        if (builder := EntriesUIRegistry.get_button_builder(type(ctx.entry))) is None:
            raise LookupError(f'Unknown entry type {type(ctx.entry)}.')

        return await builder((ctx,), data=data)