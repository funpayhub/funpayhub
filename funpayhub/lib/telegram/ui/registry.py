from __future__ import annotations

from .types import Window, Menu, PropertiesUIContext
from funpayhub.lib.properties import Properties, MutableParameter
from typing import Any, Type, TYPE_CHECKING
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
import funpayhub.lib.telegram.callbacks as cbs
import funpayhub.lib.properties.parameter as param
from . import default_ui as default

if TYPE_CHECKING:
    from .types import OneStepPropertiesUIBuilder, PropertiesUIBuilder


class UIRegistry:
    def __init__(self):
        self.default_properties_renderers: dict[type[MutableParameter | Properties], Any] = {
            param.ToggleParameter: default.TOGGLE_UI,
            param.IntParameter: default.MANUAL_CHANGE_PARAM_UI,
            param.FloatParameter: default.MANUAL_CHANGE_PARAM_UI,
            param.StringParameter: default.MANUAL_CHANGE_PARAM_UI,
            Properties: default.PROPERTIES_UI
        }
        self.properties_renderers_overloads: dict[type[MutableParameter | Properties], Any] = {}

        self.menus: dict[str, Menu] = {}
        self.menus_overloads: dict[str, Menu] = {}

    async def build_properties_ui(
        self,
        ctx: PropertiesUIContext,
        hashinator: HashinatorT1000,
        data: dict[str, Any]
    ) -> Window:
        """
        :param ctx:
        :return:
        """
        if type(ctx.entry) in self.default_properties_renderers:
            ui = self.default_properties_renderers[type(ctx.entry)]
        else:
            for entry_type, ui_builder in self.default_properties_renderers.items():
                if isinstance(ctx.entry, entry_type):
                    ui = ui_builder
                    break
            else:
                raise ValueError(f'Unknown entry type {type(ctx.entry)}.')

        menu: Menu = await ui.next_menu(self, ctx)
        keyboard = await menu.total_keyboard(self, ctx, data, convert=True)

        if keyboard:
            for line in keyboard.inline_keyboard:
                for button in line:
                    button.callback_data = cbs.Hash(
                        hash=hashinator.hash(button.callback_data)
                    ).pack()

        return Window(
            text=await menu.menu_text(self, ctx, data),
            image=await menu.menu_image(self, ctx, data),
            keyboard=keyboard,
        )

    def find_properties_builder(
        self,
        entry_type: Type[MutableParameter | Properties]
    ) -> PropertiesUIBuilder | OneStepPropertiesUIBuilder | None:
        if entry_type in self.default_properties_renderers:
            return self.default_properties_renderers[entry_type]
        else:
            for t, u in self.default_properties_renderers.items():
                if issubclass(entry_type, t):
                    return u
