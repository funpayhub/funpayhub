from __future__ import annotations


__all__ = [
    'EntriesUIRegistry'
]


from typing import TYPE_CHECKING, Type
from dataclasses import replace

from loggers import telegram_ui as logger
from funpayhub.lib.properties.base import Node
from funpayhub.lib.telegram.ui.types import Menu, Button, MenuBuilder, ButtonBuilder
from .context import EntryMenuContext as MenuCtx, EntryButtonContext as BtnCtx


if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties as Props
    from funpayhub.lib.telegram.ui import UIRegistry as UI


class _EntriesUIRegistry:
    def __init__(self) -> None:
        self._buttons: dict[type[Node], str] = {}
        """Дефолтные фабрики кнопок параметров / категорий."""

        self._menus: dict[type[Node], str] = {}
        """Дефолтные фабрики меню просмотра параметров / категорий."""

    def get_button_builder(self, entry_type: Type[Node]) -> str | None:
        if entry_type in self._buttons:
            return self._buttons[entry_type]
        for type, builder in self._buttons.items():
            if issubclass(entry_type, type):
                return builder
        return None

    def get_menu_builder(self, entry_type: Type[Node]) -> str | None:
        if entry_type in self._menus:
            return self._menus[entry_type]
        for type, builder in self._menus.items():
            if issubclass(entry_type, type):
                return builder
        return None

    def add_button_builder(
        self,
        entry_type: Type[Node],
        button_builder_id: str,
        overwrite: bool = False,
    ) -> None:
        if entry_type in self._buttons and not overwrite:
            raise KeyError(f'Button builder for entry of type {entry_type!r} already exists.')
        self._buttons[entry_type] = button_builder_id

        logger.info(
            'Button builder %s assigned as button builder for entries of type %s.',
            button_builder_id,
            entry_type,
        )

    def add_menu_builder(
        self,
        entry_type: Type[Node],
        menu_builder_id: str,
        overwrite: bool = False,
    ) -> None:
        if entry_type in self._menus and not overwrite:
            raise KeyError(f'Menu builder for entry of type {entry_type!r} already exists.')
        self._menus[entry_type] = menu_builder_id
        logger.info(
            'Menu builder %s assigned as menu builder for entries of type %r.',
            menu_builder_id,
            entry_type,
        )


EntriesUIRegistry = _EntriesUIRegistry()


class PropertiesEntryMenuBuilder(MenuBuilder, menu_id='props_entry', context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, tg_ui: UI, properties: Props) -> Menu:
        entry = properties.get_node(ctx.entry_path)
        if (builder_id := EntriesUIRegistry.get_menu_builder(type(entry))) is None:
            raise LookupError(f'Unknown entry type {type(entry)}.')
        context = replace(ctx, menu_id=builder_id)
        return await tg_ui.build_menu(context, finalize=False)


class PropertiesEntryButtonBuilder(ButtonBuilder,button_id='props_entry',  context_type=BtnCtx):
    async def build(self, ctx: BtnCtx, tg_ui: UI, properties: Props) -> Button:
        entry = properties.get_node(ctx.entry_path)
        if (builder_id := EntriesUIRegistry.get_button_builder(type(entry))) is None:
            raise LookupError(f'Unknown entry type {type(entry)}.')
        context = replace(ctx, button_id=builder_id)
        return await tg_ui.build_button(context)
