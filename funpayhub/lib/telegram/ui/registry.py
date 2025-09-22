from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type

import funpayhub.lib.telegram.callbacks as cbs
import funpayhub.lib.properties.parameter as param
from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
from funpayhub.lib.translater import Translater
from eventry.asyncio.callable_wrappers import CallableWrapper

from . import default_ui as default
from .types import Menu, Window, PropertiesUIContext, Button


class UIRegistry:
    def __init__(self, hashinator: HashinatorT1000, translater: Translater) -> None:
        self.hashinator = hashinator
        self.translater = translater

        self.default_properties_buttons: dict[
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

        self.default_properties_menus: dict[
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

        self.properties_buttons_overrides: list[CallableWrapper[Button]]
        self.properties_menus_overrides: list[CallableWrapper[Menu]]

    async def build_properties_menu(
        self,
        ctx: PropertiesUIContext,
        data: dict[str, Any],
    ) -> Window:
        builder = self.find_properties_menu_builder(type(ctx.entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(ctx.entry)}.')

        menu: Menu = await builder((self, ctx), data=data)
        keyboard = await menu.total_keyboard(self, ctx, data, convert=True)

        if keyboard:
            for line in keyboard.inline_keyboard:
                for button in line:
                    button.callback_data = cbs.Hash(
                        hash=self.hashinator.hash(button.callback_data),
                    ).pack()

        return Window(
            text=await menu.menu_text(self, ctx, data),
            image=await menu.menu_image(self, ctx, data),
            keyboard=keyboard,
        )

    def find_properties_btn_builder(
        self,
        entry_type: Type[MutableParameter | Properties],
    ) -> CallableWrapper[Button] | None:
        if entry_type in self.default_properties_buttons:
            return self.default_properties_buttons[entry_type]
        for t, u in self.default_properties_buttons.items():
            if issubclass(entry_type, t):
                return u

    def find_properties_menu_builder(
        self,
        entry_type: Type[MutableParameter | Properties],
    ) -> CallableWrapper[Menu] | None:
        if entry_type in self.default_properties_menus:
            return self.default_properties_menus[entry_type]
        for t, u in self.default_properties_menus.items():
            if issubclass(entry_type, t):
                return u
