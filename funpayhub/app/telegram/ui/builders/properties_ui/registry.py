from __future__ import annotations


__all__ = ['EntriesUIRegistry']


from typing import TYPE_CHECKING, Any, Type
from dataclasses import replace

from funpayhub.loggers import telegram_ui as logger
from funpayhub.app.telegram.ui.ids import MenuIds, ButtonIds
from funpayhub.lib.properties.base import Entry
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, ButtonBuilder
from funpayhub.app.telegram.ui.builders.properties_ui.context import (
    EntryMenuContext,
    EntryButtonContext,
)


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


class _EntriesUIRegistry:
    def __init__(self) -> None:
        self._buttons: dict[type[Entry], str] = {}
        """Дефолтные фабрики кнопок параметров / категорий."""

        self._menus: dict[type[Entry], str] = {}
        """Дефолтные фабрики меню просмотра параметров / категорий."""

    def get_button_builder(self, entry_type: Type[Entry]) -> str | None:
        if entry_type in self._buttons:
            return self._buttons[entry_type]
        for type, builder in self._buttons.items():
            if issubclass(entry_type, type):
                return builder
        return None

    def get_menu_builder(self, entry_type: Type[Entry]) -> str | None:
        if entry_type in self._menus:
            return self._menus[entry_type]
        for type, builder in self._menus.items():
            if issubclass(entry_type, type):
                return builder
        return None

    def add_button_builder(
        self,
        entry_type: Type[Entry],
        button_builder_id: str,
        overwrite: bool = False,
    ) -> None:
        if entry_type in self._buttons and not overwrite:
            raise KeyError(f'Button builder for entry of type {entry_type!r} already exists.')
        self._buttons[entry_type] = button_builder_id

        logger.info(
            f'Button builder {button_builder_id} assigned as button builder for entries '
            f'of type {entry_type!r}.',
        )

    def add_menu_builder(
        self,
        entry_type: Type[Entry],
        menu_builder_id: str,
        overwrite: bool = False,
    ) -> None:
        if entry_type in self._menus and not overwrite:
            raise KeyError(f'Menu builder for entry of type {entry_type!r} already exists.')
        self._menus[entry_type] = menu_builder_id
        logger.info(
            f'Menu builder {menu_builder_id} assigned as menu builder for entries '
            f'of type {entry_type!r}.',
        )


EntriesUIRegistry = _EntriesUIRegistry()


class PropertiesEntryMenuBuilder(MenuBuilder):
    id = MenuIds.properties_entry
    context_type = EntryMenuContext

    async def build(self, ctx: EntryMenuContext, tg_ui: UIRegistry, data: dict[str, Any]) -> Menu:
        if (builder_id := EntriesUIRegistry.get_menu_builder(type(ctx.entry))) is None:
            raise LookupError(f'Unknown entry type {type(ctx.entry)}.')
        context = replace(ctx, menu_id=builder_id)
        return await tg_ui.build_menu(context, data, finalize=False)


class PropertiesEntryButtonBuilder(ButtonBuilder):
    id = ButtonIds.properties_entry
    context_type = EntryButtonContext

    async def build(
        self, ctx: EntryButtonContext, tg_ui: UIRegistry, data: dict[str, Any]
    ) -> Button:
        if (builder_id := EntriesUIRegistry.get_button_builder(type(ctx.entry))) is None:
            raise LookupError(f'Unknown entry type {type(ctx.entry)}.')
        context = replace(ctx, button_id=builder_id)
        return await tg_ui.build_button(context, data)
