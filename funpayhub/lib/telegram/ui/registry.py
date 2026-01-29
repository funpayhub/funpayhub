from __future__ import annotations


__all__ = ['UIRegistry']


from typing import Any, Type
from dataclasses import field, dataclass

from eventry.asyncio.callable_wrappers import CallableWrapper

from loggers import telegram_ui as logger

from .types import (
    Menu,
    Button,
    MenuBuilder,
    MenuContext,
    ButtonBuilder,
    ButtonContext,
    MenuModification,
    ButtonModification,
)
from ..callback_data import HashinatorT1000


@dataclass
class _MenuBuilder:
    builder: MenuBuilder[Any]
    modifications: dict[str, MenuModification[Any]] = field(default_factory=dict)

    async def build(
        self,
        context: MenuContext,
        data: dict[str, Any],
        run_modifications: bool = True,
        finalize: bool = True,
    ) -> Menu:
        result = await self.builder(context, data)

        if run_modifications:
            for i in self.modifications.values():
                try:
                    result = await i(context, result, data)
                except:
                    continue  # todo: logging

        if finalize and result.finalizer:
            try:
                wrapped = CallableWrapper(result.finalizer)
                result = await wrapped((context, result), data)
            except:
                pass  # todo: logging
            result.finalizer = None
        return result


@dataclass
class _ButtonBuilder:
    builder: ButtonBuilder[Any]
    modifications: dict[str, ButtonModification[Any]] = field(default_factory=dict)

    async def build(
        self,
        context: ButtonContext,
        data: dict[str, Any],
        run_modifications: bool = True,
    ) -> Button:
        result = await self.builder(context, data)

        if run_modifications:
            for i in self.modifications.values():
                try:
                    result = await i(context, result, data)
                except:
                    continue  # todo: logging

        return result


class UIRegistry:
    def __init__(self, workflow_data: dict[str, Any] | None = None) -> None:
        self._menus: dict[str, _MenuBuilder] = {}
        self._buttons: dict[str, _ButtonBuilder] = {}
        self._workflow_data: dict[str, Any] = workflow_data if workflow_data is not None else {}

    def add_menu_builder(self, builder: Type[MenuBuilder[Any]], overwrite: bool = False) -> None:
        if not isinstance(builder, type) or not issubclass(builder, MenuBuilder):
            raise ValueError(
                f'Menu builder must be a subclass of MenuBuilder, got {type(builder).__name__}.',
            )

        if builder.menu_id in self._menus and not overwrite:
            raise KeyError(f'Menu {builder.menu_id!r} already exists.')

        logger.info('Adding menu builder %s to registry...', builder.menu_id)
        self._menus[builder.menu_id] = _MenuBuilder(builder())

    def add_menu_modification(
        self,
        modification: Type[MenuModification[Any]],
        menu_id: str,
    ) -> None:
        if not isinstance(modification, type) or not issubclass(modification, MenuModification):
            raise ValueError(
                f'Menu modification must be a subclass of MenuModification, '
                f'got {type(modification).__name__}.',
            )
        if menu_id not in self._menus:
            raise KeyError(f'Menu {menu_id!r} does not exist.')
        if modification.modification_id in self._menus[menu_id].modifications:
            raise KeyError(
                f'Menu {menu_id!r} already has a modification {modification.modification_id!r}.',
            )
        self._menus[menu_id].modifications[modification.modification_id] = modification()

    def get_menu_builder(self, menu_id: str) -> _MenuBuilder:
        return self._menus[menu_id]

    async def build_menu(
        self,
        context: MenuContext,
        data: dict[str, Any] | None = None,
        run_modifications: bool = True,
        finalize: bool = True,
    ) -> Menu:
        try:
            builder = self.get_menu_builder(context.menu_id)
        except KeyError:
            logger.error('Menu %s not found.', context.menu_id)
            raise  # todo: custom error

        if not isinstance(context, builder.builder.context_type):
            raise TypeError(
                f'Menu {context.menu_id!r} requires context of type {builder.builder.context_type!r}, '
                f'not {type(context)!r}.',
            )

        logger.info('Building menu %s.', context.menu_id)

        # create new workflow data object and replace 'data' key

        result = await builder.build(
            context,
            self._workflow_data,
            run_modifications=run_modifications,
            finalize=finalize,
        )
        HashinatorT1000.save()
        return result

    def add_button_builder(
        self,
        builder: Type[ButtonBuilder[Any]],
        overwrite: bool = False,
    ) -> None:
        if not isinstance(builder, type) or not issubclass(builder, ButtonBuilder):
            raise ValueError(
                f'Button builder must be a subclass of ButtonBuilder, '
                f'got {type(builder).__name__}.',
            )
        if builder.button_id in self._buttons and not overwrite:
            raise KeyError(f'Button {builder.button_id!r} already exists.')

        logger.info('Adding button builder %s to registry...', builder.button_id)
        self._buttons[builder.button_id] = _ButtonBuilder(builder())

    def add_button_modification(
        self,
        modification: Type[ButtonModification[Any]],
        button_id: str,
    ) -> None:
        if not isinstance(modification, type) or not issubclass(modification, ButtonModification):
            raise ValueError(
                f'Button modification must be a subclass of ButtonModification, '
                f'got {type(modification).__name__}.',
            )

        if button_id not in self._buttons:
            raise KeyError(f'Button {button_id!r} does not exist.')
        if modification.modification_id in self._buttons[button_id].modifications:
            raise KeyError(
                f'Button {button_id!r} already has a modification {modification.modification_id!r}.',
            )
        self._buttons[button_id].modifications[modification.modification_id] = modification()
        logger.info(
            'Modification %s for button %s has been added to registry.',
            modification.modification_id,
            button_id,
        )

    def get_button_builder(self, button_id: str) -> _ButtonBuilder:
        return self._buttons[button_id]

    async def build_button(
        self,
        context: ButtonContext,
        data: dict[str, Any] | None = None,
        run_modifications: bool = True,
    ) -> Button:
        try:
            builder = self.get_button_builder(context.button_id)
        except KeyError:
            logger.error('Button %s not found.', context.button_id)
            raise

        if not isinstance(context, builder.builder.context_type):
            raise TypeError(
                f'Menu {context.button_id!r} requires context of type {builder.builder.context_type!r}, '
                f'not {type(context)!r}.',
            )

        logger.info('Building button %s.', context.button_id)

        return await builder.build(
            context,
            self._workflow_data,
            run_modifications=run_modifications,
        )
