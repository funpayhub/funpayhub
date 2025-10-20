from __future__ import annotations


__all__ = ['PropertiesUIRegistry']


from typing import Any, Type, TYPE_CHECKING
from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.app.telegram.ui.builders.properties_ui.context import PropertiesMenuRenderContext, \
    PropertiesButtonRenderContext
from funpayhub.lib.properties.base import Entry
from funpayhub.loggers import telegram_ui as logger

from funpayhub.lib.telegram.ui.types import Menu, Button, ButtonBuilderProto, MenuBuilderProto

if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui.registry import UIRegistry


class _PropertiesUIRegistry:
    def __init__(self) -> None:
        self._buttons: dict[type[Entry], CallableWrapper[Button]] = {}
        """Дефолтные фабрики кнопок параметров / категорий."""

        self._menus: dict[type[Entry], CallableWrapper[Menu]] = {}
        """Дефолтные фабрики меню просмотра параметров / категорий."""

    async def build_menu(
        self,
        registry: UIRegistry,
        ctx: PropertiesMenuRenderContext,
        data: dict[str, Any]
    ) -> Menu:
        logger.debug(f'Properties menu builder for {ctx.entry.path} ({type(ctx.entry).__name__}) '
                     f'has been requested.')

        builder = self.get_menu_builder(type(ctx.entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(ctx.entry)}.')

        result = await builder((registry, ctx), data=data)
        return result

    async def build_button(
        self,
        registry: UIRegistry,
        ctx: PropertiesButtonRenderContext,
        data: dict[str, Any]) -> Button:
        logger.debug(f'Properties button builder for {ctx.entry.path} ({type(ctx.entry).__name__}) '
                     f'has been requested.')

        builder = self.get_button_builder(type(ctx.entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(ctx.entry)}.')

        result = await builder((registry, ctx), data=data)
        return result

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
        builder: ButtonBuilderProto,
        overwrite: bool = False
    ) -> None:
        if entry_type in self._buttons:
            if not overwrite:
                raise KeyError(f'Properties button builder for {entry_type.__name__!r} already exists.')
        self._buttons[entry_type] = CallableWrapper(builder)
        logger.info(
            f'Properties entry button builder for {entry_type.__name__!r} '
            f'has been added to properties ui registry.'
        )

    def add_menu_builder(
        self,
        entry_type: Type[Entry],
        builder: MenuBuilderProto,
        overwrite: bool = False
    ) -> None:
        if entry_type in self._menus:
            if not overwrite:
                raise KeyError(f'Properties menu builder for {entry_type.__name__!r} already exists.')
        self._menus[entry_type] = CallableWrapper(builder)
        logger.info(
            f'Properties entry menu builder for {entry_type.__name__!r} '
            f'has been added to properties ui registry.'
        )

PropertiesUIRegistry = _PropertiesUIRegistry()
