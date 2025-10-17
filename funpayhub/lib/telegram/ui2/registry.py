from __future__ import annotations


__all__ = ['UIRegistry']


from typing import Any, Protocol

from eventry.asyncio.callable_wrappers import CallableWrapper
from funpayhub.loggers import telegram_ui as logger

from .types import Menu, Button, MenuRenderContext, ButtonRenderContext
from .types import (
    MenuBuilderProto,
    MenuModFilterProto,
    MenuModProto,
    ButtonBuilderProto,
    ButtonModFilterProto,
    ButtonModProto,
    MenuBuilder,
    MenuModification,
    ButtonBuilder,
    ButtonModification,
)


class UIRegistry:
    def __init__(self, workflow_data: dict[str, Any] | None = None) -> None:
        self._menus: dict[str, MenuBuilder] = {}
        self._buttons: dict[str, ButtonBuilder] = {}  # todo

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

        self._menus[menu_id] = MenuBuilder(CallableWrapper(builder), mods)
        logger.info(f'Menu builder {menu_id!r} has been added to registry.')

    def add_menu_modification(
        self,
        menu_id: str,
        modification_id: str,
        modification: MenuModProto,
        filter: MenuModFilterProto | None = None,
    ) -> None:
        if menu_id not in self._menus:
            raise KeyError(f'Menu {menu_id!r} does not exist.')
        if modification_id in self._menus[menu_id].modifications:
            raise KeyError(f'Menu {menu_id!r} already has a modification {modification_id!r}.')

        modification_obj = MenuModification(
            CallableWrapper(modification),
            CallableWrapper(filter) if filter is not None else None
        )
        self._menus[menu_id].modifications[modification_id] = modification_obj
        logger.info(
            f'Modification {modification_id!r} for menu {menu_id!r} '
            f'has been added to registry.'
        )

    def get_menu_builder(self, menu_id: str) -> MenuBuilder:
        return self._menus[menu_id]

    async def build_menu(self, context: MenuRenderContext, data: dict[str, Any]) -> Menu:
        try:
            builder = self.get_menu_builder(context.menu_id)
        except KeyError:
            logger.error(f'Menu {context.menu_id!r} not found.')
            raise

        logger.info(f'Building menu {context.menu_id!r}.')

        data = self._workflow_data | data
        data['data'] = data

        return await builder.build(self, context, data)

    def add_button_builder(
        self,
        button_id: str,
        builder: ButtonBuilderProto,
        overwrite: bool = False
    ) -> None:
        mods = {}
        if button_id in self._buttons:
            if overwrite:
                raise KeyError(f'Button {button_id!r} already exists.')
            mods = self._buttons[button_id].modifications

        self._buttons[button_id] = ButtonBuilder(CallableWrapper(builder), mods)
        logger.info(f'Button builder {button_id!r} has been added to registry.')

    def add_button_modification(
        self,
        button_id: str,
        modification_id: str,
        modification: ButtonModProto,
        filter: ButtonModFilterProto | None = None,
    ) -> None:
        if button_id not in self._buttons:
            raise KeyError(f'Button {button_id!r} does not exist.')
        if modification_id in self._buttons[button_id].modifications:
            raise KeyError(f'Button {button_id!r} already has a modification {modification_id!r}.')

        modification_obj = ButtonModification(
            CallableWrapper(modification),
            CallableWrapper(filter) if filter is not None else None
        )
        self._buttons[button_id].modifications[modification_id] = modification_obj
        logger.info(
            f'Modification {modification_id!r} for button {button_id!r} '
            f'has been added to registry.'
        )

    def get_button_builder(self, button_id: str) -> ButtonBuilder:
        return self._buttons[button_id]

    async def build_button(
        self,
        button_id: str,
        context: MenuRenderContext,
        context_data: dict[str, Any],
        data: dict[str, Any]
    ) -> Button:
        try:
            builder = self.get_button_builder(button_id)
        except KeyError:
            logger.error(f'Button {button_id!r} not found.')
            raise

        logger.info(f'Building button {button_id!r}.')

        data = self._workflow_data | data
        data['data'] = data

        button_context = ButtonRenderContext(
            button_id=button_id,
            menu_render_context=context,
            data=context_data
        )

        return await builder.build(self, button_context, data)
