from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type, Concatenate, ParamSpec

import funpayhub.lib.properties.parameter as param
from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
from funpayhub.lib.translater import Translater
from eventry.asyncio.callable_wrappers import CallableWrapper
from collections.abc import Callable, Awaitable

from . import default_ui as default
from .types import Menu, PropertiesUIContext, Button


P = ParamSpec('P')

type EntryBtnBuilder = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, P],
    Button | Awaitable[Button]
]

type EntryMenuBuilder = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, P],
    Menu | Awaitable[Menu]
]

type EntryBtnModification = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, Button, P],
    Button | Awaitable[Button]
]

type EntryMenuModification = Callable[
    Concatenate[UIRegistry, PropertiesUIContext, Menu, P],
    Menu | Awaitable[Menu]
]


class UIRegistry:
    def __init__(self, hashinator: HashinatorT1000, translater: Translater) -> None:
        self.hashinator = hashinator
        self.translater = translater

        self.default_entries_buttons: dict[
            type[MutableParameter | Properties],
            CallableWrapper[Button]
        ] = {
            param.ToggleParameter: default.TOGGLE_BTN,
            param.IntParameter: default.INT_PARAM_BTN,
            param.FloatParameter: default.FLOAT_PARAM_BTN,
            param.StringParameter: default.STRING_PARAM_BTN,
            param.ChoiceParameter: default.CHOICE_PARAM_BTN,
            Properties: default.PROPERTIES_BTN
        }
        """Дефолтные фабрики кнопок параметров / категорий."""

        self.default_entry_menus: dict[
            type[MutableParameter | Properties],
            CallableWrapper[Menu]
        ] = {
            param.IntParameter: default.INT_PARAM_MENU,
            param.FloatParameter: default.FLOAT_PARAM_MENU,
            param.StringParameter: default.STRING_PARAM_MENU,
            param.ChoiceParameter: default.CHOICE_PARAM_MENU,
            Properties: default.PROPERTIES_MENU
        }
        """Дефолтные фабрики меню параметров / категорий."""

        self.entries_buttons_modifications: dict[str, CallableWrapper[Button]] = {}
        self.entries_menus_modifications: dict[str, CallableWrapper[Menu]] = {}

    async def build_properties_menu(
        self,
        ctx: PropertiesUIContext,
        data: dict[str, Any],
    ) -> Menu:
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
        data: dict[str, Any]
    ):
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
        modification: EntryMenuModification
    ):
        self.entries_menus_modifications[modification_id] = CallableWrapper(modification)
