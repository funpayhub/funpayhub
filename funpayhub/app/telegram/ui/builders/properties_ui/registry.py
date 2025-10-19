from __future__ import annotations


__all__ = ['PropertiesUIRegistry']


from typing import Any, Type, TYPE_CHECKING
from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.properties.base import Entry
from funpayhub.loggers import telegram_ui as logger

from funpayhub.lib.telegram.ui.types import Menu, Button, MenuRenderContext, ButtonRenderContext, \
    ButtonBuilderProto, MenuBuilderProto

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
        ctx: MenuRenderContext,
        entry: Entry,
        data: dict[str, Any]
    ) -> Menu:
        logger.debug(f'Properties menu builder for {entry.path} ({type(entry).__name__}) '
                     f'has been requested.')

        builder = self.get_menu_builder(type(entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(entry)}.')

        result = await builder((registry, ctx), data=data)
        return result

    async def build_button(
        self,
        registry: UIRegistry,
        ctx: ButtonRenderContext,
        entry: Entry,
        data: dict[str, Any]) -> Button:
        logger.debug(f'Properties button builder for {entry.path} ({type(entry).__name__}) '
                     f'has been requested.')

        builder = self.get_button_builder(type(entry))
        if builder is None:
            raise ValueError(f'Unknown entry type {type(entry)}.')

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

    async def entry_menu_builder(
        self,
        registry: UIRegistry,
        ctx: MenuRenderContext,
        properties: FunPayHubProperties,
        data: dict[str, Any]
    ) -> Menu:
        """
        Реальный menu builder, который необходимо зарегистрировать в UIRegistry с ID
        `MenuIds.properties_entry`.
        """
        if 'path' not in ctx.data:
            raise RuntimeError('Unable to build properties entry menu: \'path\' is missing.')
        entry = properties.get_entry(ctx.data['path'])

        if entry is None:
            raise RuntimeError(
                f'Unable to build properties entry menu: '
                f'no entry with path {ctx.data['path']}.'
            )

        ctx.data['entry'] = entry
        return await self.build_menu(registry, ctx, entry, {**data})

    async def entry_button_builder(
        self,
        registry: UIRegistry,
        ctx: ButtonRenderContext,
        properties: FunPayHubProperties,
        data: dict[str, Any]
    ) -> Button:
        if 'path' not in ctx.data:
            raise RuntimeError('Unable to build properties entry button: \'path\' is missing.')
        entry = properties.get_entry(ctx.data['path'])

        if entry is None:
            raise RuntimeError(
                f'Unable to build properties entry button: '
                f'no entry with path {ctx.data['path']}.'
            )

        ctx.data['entry'] = entry
        return await self.build_button(registry, ctx, entry, {**data})


PropertiesUIRegistry = _PropertiesUIRegistry()
