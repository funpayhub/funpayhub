from __future__ import annotations


__all__ = ['UIRegistry']


from typing import Any, Type, Concatenate
from collections.abc import Callable, Awaitable

from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.translater import Translater
from funpayhub.loggers import telegram_ui as logger

from .types import Menu, Button, UIContext, PropertiesUIContext


type EntryBtnBuilder[**P] = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, P],
    Button | Awaitable[Button],
]

type EntryMenuBuilder[**P] = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, P],
    Menu | Awaitable[Menu],
]

type EntryBtnModification[**P] = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, Button, P],
    Button | Awaitable[Button],
]

type EntryMenuModification[**P] = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, Menu, P],
    Menu | Awaitable[Menu],
]

# Menus
type MenuBtnBuilder[**P] = Callable[
    Concatenate[UIRegistry, UIContext, P],
    Button | Awaitable[Button],
]

type MenuBuilder[**P] = Callable[
    Concatenate[UIRegistry, UIContext, P],
    Menu | Awaitable[Menu],
]


class UIRegistry:
    def __init__(self, translater: Translater) -> None:
        self.translater = translater

        self.default_entries_buttons: dict[
            type[MutableParameter | Properties],
            CallableWrapper[Button],
        ] = {}
        """Дефолтные фабрики кнопок параметров / категорий."""

        self.default_entries_menus: dict[
            type[MutableParameter | Properties],
            CallableWrapper[Menu],
        ] = {}
        """Дефолтные фабрики меню параметров / категорий."""

        self.entries_buttons_modifications: dict[str, CallableWrapper[Button]] = {}
        self.entries_menus_modifications: dict[str, CallableWrapper[Menu]] = {}

        self.default_menus: dict[str, CallableWrapper[Menu]] = {}

    async def build_properties_menu(
        self,
        ctx: PropertiesUIContext,
        data: dict[str, Any],
    ) -> Menu:
        logger.debug(f'Properties menu builder for {ctx.entry.path} ({type(ctx.entry).__name__}) '
                     f'has been requested.')

        builder = self.find_properties_menu_builder(type(ctx.entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(ctx.entry)}.')

        result = await builder((self, ctx), data=data)

        # todo: add logging for modifications
        for modification_id, modification in self.entries_menus_modifications.items():
            try:
                result = await modification((self, ctx, result), data=data)
            except:
                import traceback
                print(f'An error occurred while modifying properties menu.')
                print(traceback.format_exc())
                continue

        if result.finalizer:
            finalizer = CallableWrapper(result.finalizer)
            result = await finalizer((self, ctx, result), data=data)

        return result

    async def build_properties_button(
        self,
        ctx: PropertiesUIContext,
        data: dict[str, Any],
    ) -> Button:
        logger.debug(f'Properties button builder for {ctx.entry.path} ({type(ctx.entry).__name__}) '
                     f'has been requested.')

        builder = self.find_properties_btn_builder(type(ctx.entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(ctx.entry)}.')

        result = await builder((self, ctx), data=data)

        # todo: add logging for modifications
        for modification_id, modification in self.entries_buttons_modifications.items():
            try:
                result = await modification((self, ctx, result), data=data)
            except:
                continue
        return result

    async def build_menu(
        self,
        menu_id: str,
        ctx: UIContext,
        data: dict[str, Any],
    ) -> Menu:
        logger.debug(f'Properties menu builder {menu_id!r} has been requested.')
        if menu_id not in self.default_menus:
            raise ValueError(f'Unknown menu id {menu_id}.')

        result = await self.default_menus[menu_id]((self, ctx), data=data)
        if result.finalizer:
            finalizer = CallableWrapper(result.finalizer)
            result = await finalizer((self, ctx, result), data=data)
        return result

    def find_properties_btn_builder(
        self,
        entry_type: Type[MutableParameter | Properties],
    ) -> CallableWrapper[Button] | None:
        if entry_type in self.default_entries_buttons:
            return self.default_entries_buttons[entry_type]
        for t, u in self.default_entries_buttons.items():
            if issubclass(entry_type, t):
                return u

    def find_properties_menu_builder(
        self,
        entry_type: Type[MutableParameter | Properties],
    ) -> CallableWrapper[Menu] | None:
        if entry_type in self.default_entries_menus:
            return self.default_entries_menus[entry_type]
        for t, u in self.default_entries_menus.items():
            if issubclass(entry_type, t):
                return u

    def add_default_entry_button_builder(
        self,
        entry_type: Type[Properties | MutableParameter],
        builder: EntryBtnBuilder,
    ):
        if entry_type in self.default_entries_buttons:
            raise ValueError(f'Default button builder for {entry_type} is already added.')
        self.default_entries_buttons[entry_type] = CallableWrapper(builder)

    def set_default_entry_menu_builder(
        self,
        entry_type: Type[Properties | MutableParameter],
        builder: EntryMenuBuilder,
    ):
        if entry_type in self.default_entries_menus:
            raise ValueError(f'Default menu builder for {entry_type} is already added.')
        self.default_entries_menus[entry_type] = CallableWrapper(builder)

    def add_entry_button_modification(
        self,
        modification_id: str,
        modification: EntryBtnModification,
    ):
        self.entries_buttons_modifications[modification_id] = CallableWrapper(modification)

    def add_entry_menu_modification(
        self,
        modification_id: str,
        modification: EntryMenuModification,
    ):
        self.entries_menus_modifications[modification_id] = CallableWrapper(modification)

    def add_menu(
        self,
        menu_id: str,
        builder: MenuBuilder,
    ):
        if menu_id in self.default_menus:
            raise ValueError(f'Default menu with ID {menu_id!r} is already added.')
        self.default_menus[menu_id] = CallableWrapper(builder)
