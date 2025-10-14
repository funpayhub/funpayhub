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
    def __init__(self) -> None:
        self.menus: dict[str, CallableWrapper[Menu]] = {}
        self.modifications: dict[str, list[CallableWrapper[Menu]]] = {}
        self.properties_ui_registry = PropertiesUIRegistry()

    async def build_menu(
        self,
        menu_id: str,
        ctx: UIContext,
        data: dict[str, Any],
    ) -> Menu:
        logger.debug(f'Properties menu builder {menu_id!r} has been requested.')
        if menu_id not in self.menus:
            raise ValueError(f'Unknown menu id {menu_id}.')

        result = await self.menus[menu_id]((self, ctx), data=data)
        if result.finalizer:
            finalizer = CallableWrapper(result.finalizer)
            result = await finalizer((self, ctx, result), data=data)
        return result

    def add_menu(
        self,
        menu_id: str,
        builder: MenuBuilder,
    ) -> None:
        if menu_id in self.menus:
            raise ValueError(f'Menu {menu_id!r} already exists.')
        self.menus[menu_id] = CallableWrapper(builder)

    def add_modification(self, menu_id: str, modification_id: str, builder: MenuBuilder) -> None:
        ...


class PropertiesUIRegistry:
    def __init__(self) -> None:
        self.entries_buttons_builders: dict[
            type[MutableParameter[Any] | Properties],
            CallableWrapper[Button],
        ] = {}

        self.entries_menus_builders: dict[
            type[MutableParameter[Any] | Properties],
            CallableWrapper[Menu],
        ] = {}

    def button_builder(
        self,
        entry_type: Type[MutableParameter[Any] | Properties]
    ) -> CallableWrapper[Button] | None:
        if entry_type in self.entries_buttons_builders:
            return self.entries_buttons_builders[entry_type]
        for t, u in self.entries_buttons_builders.items():
            if issubclass(entry_type, t):
                return u
        return None

    def menu_builder(
        self,
        entry_type: Type[MutableParameter[Any] | Properties],
    ) -> CallableWrapper[Menu] | None:
        if entry_type in self.entries_menus_builders:
            return self.entries_menus_builders[entry_type]
        for t, u in self.entries_menus_builders.items():
            if issubclass(entry_type, t):
                return u
        return None
