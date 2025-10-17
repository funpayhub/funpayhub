from __future__ import annotations


__all__ = ['PropertiesUIRegistry']


from typing import Any, Type, Concatenate
from collections.abc import Callable, Awaitable

from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.loggers import telegram_ui as logger

from funpayhub.lib.telegram.ui2.types import Menu, Button, UIRenderContext


class PropertiesUIRegistry:
    def __init__(self, properties: Properties) -> None:
        self.buttons: dict[type[MutableParameter[Any] | Properties], CallableWrapper[Button]] = {}
        """Дефолтные фабрики кнопок параметров / категорий."""

        self.menus: dict[type[MutableParameter[Any] | Properties], CallableWrapper[Menu]] = {}
        """Дефолтные фабрики меню просмотра параметров / категорий."""

        self._properties = properties

    async def build_menu(self, ctx: UIRenderContext, data: dict[str, Any]) -> Menu:
        if 'entry_path' not in ctx.data:
            raise RuntimeError('Unable to build properties menu: \'entry_path\' is missing.')

        entry = self._properties.get_entry(ctx.data['entry_path'])

        logger.debug(f'Properties menu builder for {entry.path} ({type(entry).__name__}) '
                     f'has been requested.')

        builder = self.get_menu_builder(type(entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(entry)}.')

        result = await builder((self, ctx), data=data)
        return result

    async def build_button(self, ctx: UIRenderContext, data: dict[str, Any]) -> Button:
        logger.debug(f'Properties button builder for {ctx.entry.path} ({type(ctx.entry).__name__}) '
                     f'has been requested.')

        builder = self.get_button_builder(type(ctx.entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(ctx.entry)}.')

        result = await builder((self, ctx), data=data)
        return result

    def get_button_builder(
        self,
        entry_type: Type[MutableParameter | Properties],
    ) -> CallableWrapper[Button] | None:
        if entry_type in self.buttons:
            return self.buttons[entry_type]
        for t, u in self.buttons.items():
            if issubclass(entry_type, t):
                return u

    def get_menu_builder(
        self,
        entry_type: Type[MutableParameter | Properties],
    ) -> CallableWrapper[Menu] | None:
        if entry_type in self.menus:
            return self.menus[entry_type]
        for t, u in self.menus.items():
            if issubclass(entry_type, t):
                return u

    def set_button_builder(
        self,
        entry_type: Type[Properties | MutableParameter],
        builder: EntryBtnBuilder,
    ):
        if entry_type in self.buttons:
            raise ValueError(f'Default button builder for {entry_type} is already added.')
        self.buttons[entry_type] = CallableWrapper(builder)

    def set_menu_builder(
        self,
        entry_type: Type[Properties | MutableParameter],
        builder: EntryMenuBuilder,
    ):
        if entry_type in self.menus:
            raise ValueError(f'Default menu builder for {entry_type} is already added.')
        self.menus[entry_type] = CallableWrapper(builder)
