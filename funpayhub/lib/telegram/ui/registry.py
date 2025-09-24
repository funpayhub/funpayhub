from __future__ import annotations


__all__ = ['UIRegistry']


from typing import Any, Type, Concatenate
from collections.abc import Callable, Awaitable

from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000

from .types import RenderedMenu, Button, UIContext, PropertiesUIContext


type EntryBtnBuilder[**P] = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, P],
    Button | Awaitable[Button],
]

type EntryMenuBuilder[**P] = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, P],
    RenderedMenu | Awaitable[RenderedMenu],
]

type EntryBtnModification[**P] = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, Button, P],
    Button | Awaitable[Button],
]

type EntryMenuModification[**P] = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, RenderedMenu, P],
    RenderedMenu | Awaitable[RenderedMenu],
]

# Menus
type MenuBtnBuilder[**P] = Callable[
    Concatenate[UIRegistry, UIContext, P],
    Button | Awaitable[Button],
]

type MenuBuilder[**P] = Callable[
    Concatenate[UIRegistry, UIContext, P],
    RenderedMenu | Awaitable[RenderedMenu],
]


class UIRegistry:
    def __init__(self, hashinator: HashinatorT1000, translater: Translater) -> None:
        self.hashinator = hashinator
        self.translater = translater

        self.default_entries_buttons: dict[
            type[MutableParameter | Properties],
            CallableWrapper[Button],
        ] = {}
        """Дефолтные фабрики кнопок параметров / категорий."""

        self.default_entry_menus: dict[
            type[MutableParameter | Properties],
            CallableWrapper[RenderedMenu],
        ] = {}
        """Дефолтные фабрики меню параметров / категорий."""

        self.entries_buttons_modifications: dict[str, CallableWrapper[Button]] = {}
        self.entries_menus_modifications: dict[str, CallableWrapper[RenderedMenu]] = {}

        self.default_menu_buttons: dict[str, CallableWrapper[Button]] = {}
        self.default_menus: dict[str, CallableWrapper[RenderedMenu]] = {}

    async def build_properties_menu(
        self,
        ctx: PropertiesUIContext,
        data: dict[str, Any],
    ) -> RenderedMenu:
        builder = self.find_properties_menu_builder(type(ctx.entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(ctx.entry)}.')

        result = await builder((self, ctx), data=data)

        # todo: add logging for modifications
        for modification_id, modification in self.entries_menus_modifications.items():
            try:
                result = await modification((self, ctx, result), data=data)
            except:
                continue

        return result

    async def build_properties_button(
        self,
        ctx: PropertiesUIContext,
        data: dict[str, Any],
    ) -> Button:
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

    async def build_menu_button(
        self,
        menu_id: str,
        ctx: UIContext,
        data: dict[str, Any],
    ) -> Button:
        if menu_id not in self.default_menu_buttons:
            raise ValueError(f'Unknown menu id {menu_id}.')

        return await self.default_menu_buttons[menu_id]((self, ctx), data=data)

    async def build_menu(
        self,
        menu_id: str,
        ctx: UIContext,
        data: dict[str, Any],
    ) -> RenderedMenu:
        if menu_id not in self.default_menus:
            raise ValueError(f'Unknown menu id {menu_id}.')

        return await self.default_menus[menu_id]((self, ctx), data=data)

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
    ) -> CallableWrapper[RenderedMenu] | None:
        if entry_type in self.default_entry_menus:
            return self.default_entry_menus[entry_type]
        for t, u in self.default_entry_menus.items():
            if issubclass(entry_type, t):
                return u

    def set_default_entry_button_builder(
        self,
        entry_type: Type[Properties | MutableParameter],
        builder: EntryBtnBuilder,
    ):
        self.default_entries_buttons[entry_type] = CallableWrapper(builder)

    def set_default_entry_menu_builder(
        self,
        entry_type: Type[Properties | MutableParameter],
        builder: EntryMenuBuilder,
    ):
        self.default_entry_menus[entry_type] = CallableWrapper(builder)

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

    def add_menu_button(
        self,
        menu_id: str,
        builder: MenuBtnBuilder,
    ):
        self.default_menu_buttons[menu_id] = CallableWrapper(builder)

    def add_menu(
        self,
        menu_id: str,
        builder: MenuBuilder,
    ):
        self.default_menus[menu_id] = CallableWrapper(builder)
