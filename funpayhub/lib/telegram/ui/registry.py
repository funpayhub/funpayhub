from __future__ import annotations


__all__ = ['UIRegistry']


from typing import Any, Type

from funpayhub.loggers import telegram_ui as logger

from .types import (
    Menu,
    Button,
    MenuBuilder,
    MenuModProto,
    ButtonBuilder,
    ButtonModProto,
    MenuBuilderProto,
    MenuModification,
    MenuContext,
    ButtonBuilderProto,
    ButtonModification,
    MenuModFilterProto,
    ButtonContext,
    ButtonModFilterProto,
)
from ..callback_data import HashinatorT1000


class UIRegistry:
    def __init__(self, workflow_data: dict[str, Any] | None = None) -> None:
        self._menus: dict[str, MenuBuilder] = {}
        self._buttons: dict[str, ButtonBuilder] = {}
        self._workflow_data: dict[str, Any] = workflow_data if workflow_data is not None else {}

    def add_menu_builder(self,
        menu_id: str,
        builder: MenuBuilderProto,
        context_type: Type[MenuContext] = MenuContext,
        overwrite: bool = False,
    ) -> None:
        if menu_id in self._menus and not overwrite:
            raise KeyError(f'Menu {menu_id!r} already exists.')

        self._menus[menu_id] = MenuBuilder(builder, context_type)
        logger.info(f'Menu builder {menu_id!r} has been added to registry.')

    def add_menu_modification(
        self,
        menu_id: str,
        mod_id: str,
        modification: MenuModProto,
        filter: MenuModFilterProto | None = None,
    ) -> None:
        if menu_id not in self._menus:
            raise KeyError(f'Menu {menu_id!r} does not exist.')
        if mod_id in self._menus[menu_id].modifications:
            raise KeyError(f'Menu {menu_id!r} already has a modification {mod_id!r}.')

        self._menus[menu_id].modifications[mod_id] = MenuModification(modification, filter)
        logger.info(f'Modification {mod_id!r} for menu {menu_id!r} has been added to registry.')

    def get_menu_builder(self, menu_id: str) -> MenuBuilder:
        return self._menus[menu_id]

    async def build_menu(self, context: MenuContext, data: dict[str, Any]) -> Menu:
        try:
            builder = self.get_menu_builder(context.menu_id)
        except KeyError:
            logger.error(f'Menu {context.menu_id!r} not found.')
            raise  # todo: custom error

        if not isinstance(context, builder.context_type):
            raise TypeError(
                f'Menu {context.menu_id!r} requires context of type {builder.context_type!r}, '
                f'not {type(context)!r}.',
            )

        logger.info(f'Building menu {context.menu_id!r}.')

        # create new workflow data object and replace 'data' key
        data = self._workflow_data | data
        data['data'] = data

        result = await builder.build(context, data)
        HashinatorT1000.save()
        return result

    def add_button_builder(
        self,
        button_id: str,
        builder: ButtonBuilderProto,
        context_type: Type[ButtonContext] = ButtonContext,
        overwrite: bool = False,
    ) -> None:
        mods = {}
        if button_id in self._buttons:
            if not overwrite:
                raise KeyError(f'Button {button_id!r} already exists.')
            mods = self._buttons[button_id].modifications

        self._buttons[button_id] = ButtonBuilder(builder, context_type, mods)
        logger.info(f'Button builder {button_id!r} has been added to registry.')

    def add_button_modification(self,
        button_id: str,
        mod_id: str,
        modification: ButtonModProto,
        filter: ButtonModFilterProto | None = None,
    ) -> None:
        if button_id not in self._buttons:
            raise KeyError(f'Button {button_id!r} does not exist.')
        if mod_id in self._buttons[button_id].modifications:
            raise KeyError(f'Button {button_id!r} already has a modification {mod_id!r}.')
        self._buttons[button_id].modifications[mod_id] = ButtonModification(modification, filter)
        logger.info(f'Modification {mod_id!r} for button {button_id!r} has been added to registry.')

    def get_button_builder(self, button_id: str) -> ButtonBuilder:
        return self._buttons[button_id]

    async def build_button(self, context: ButtonContext, data: dict[str, Any]) -> Button:
        try:
            builder = self.get_button_builder(context.button_id)
        except KeyError:
            logger.error(f'Button {context.button_id!r} not found.')
            raise

        if not isinstance(context, builder.context_type):
            raise TypeError(
                f'Menu {context.button_id!r} requires context of type {builder.context_type!r}, '
                f'not {type(context)!r}.',
            )

        logger.info(f'Building button {context.button_id!r}.')

        data = self._workflow_data | data
        data['data'] = data

        return await builder.build(context, data)
