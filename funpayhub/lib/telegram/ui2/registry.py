from __future__ import annotations


__all__ = ['UIRegistry']


from typing import Any, Protocol

from eventry.asyncio.callable_wrappers import CallableWrapper
from funpayhub.loggers import telegram_ui as logger

from .types import Menu, Button, UIRenderContext
from dataclasses import dataclass, field


class MenuBuilderProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: UIRenderContext,
        *__args: Any,
        **__kwargs: Any
    ) -> Menu: ...


class MenuModFilterProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: UIRenderContext,
        __menu: Menu,
        *__args: Any,
        **__kwargs: Any
    ) -> bool: ...


class MenuModProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: UIRenderContext,
        __menu: Menu,
        *__args: Any,
        **__kwargs: Any
    ) -> Menu: ...


class ButtonBuilderProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: UIRenderContext,
        *__args: Any,
        **__kwargs: Any
    ) -> Button: ...


class ButtonModFilterProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: UIRenderContext,
        __button: Button,
        *__args: Any,
        **__kwargs: Any
    ) -> bool: ...


class ButtonModProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: UIRenderContext,
        __button: Button,
        *__args: Any,
        **__kwargs: Any
    ) -> Button: ...


@dataclass
class _MenuMod:
    menu_id: str
    mod_id: str
    mod: CallableWrapper[Menu]
    filter: CallableWrapper[bool] | None = None

    async def __call__(
        self,
        registry: UIRegistry,
        context: UIRenderContext,
        menu: Menu,
        data: dict[str, Any]
    ) -> Menu:
        if self.filter is not None:
            result = await self.filter((registry, context, menu), data)
            if not result:
                return menu
        return await self.mod((registry, context, menu), data)


@dataclass
class _MenuBuilder:
    menu_id: str
    builder: CallableWrapper[Menu]
    modifications: dict[str, _MenuMod] = field(default_factory=dict)

    async def build(self, registry: UIRegistry, context: UIRenderContext, data: dict[str, Any]) -> Menu:
        result = await self.builder((registry, context), data)
        if not self.modifications:
            return result
        for i in self.modifications.values():
            try:
                result = await i(registry, context, result, data)
            except:
                continue  # todo: logging
        return result


@dataclass
class _ButtonMod:
    button_id: str
    mod_id: str
    mod: CallableWrapper[Button]
    filter: CallableWrapper[bool] | None = None


class _ButtonBuilder:
    button_id: str
    builder: CallableWrapper[Button]
    modifications: dict[str, _ButtonMod] = field(default_factory=dict)


class UIRegistry:
    def __init__(self, workflow_data: dict[str, Any] | None = None) -> None:
        self._menus: dict[str, _MenuBuilder] = {}
        self._buttons: dict[str, _MenuBuilder] = {}  # todo

        self._workflow_data: dict[str, Any] = workflow_data if workflow_data is not None else {}

    def add_menu_builder(
        self,
        menu_id: str,
        builder: MenuBuilderProto,
        overwrite: bool = False
    ) -> None:
        mods = {}
        if menu_id in self._menus:
            if overwrite:
                raise KeyError(f'Menu {menu_id!r} already exists.')
            mods = self._menus[menu_id].modifications

        self._menus[menu_id] = _MenuBuilder(menu_id, CallableWrapper(builder), mods)

    def get_menu_builder(self, menu_id: str) -> _MenuBuilder:
        return self._menus[menu_id]

    async def build_menu(self, context: UIRenderContext, data: dict[str, Any]) -> Menu:
        try:
            builder = self.get_menu_builder(context.menu_id)
        except KeyError:
            logger.error(f'Menu {context.menu_id!r} not found.')
            raise

        logger.info(f'Building menu {context.menu_id!r}.')

        data = self._workflow_data | data
        data['data'] = data

        return await builder.build(self, context, data)
