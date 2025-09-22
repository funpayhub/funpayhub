from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, ParamSpec, Concatenate, overload
from dataclasses import dataclass
from collections.abc import Callable, Awaitable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.translater import Translater


if TYPE_CHECKING:
    from .registry import UIRegistry


type Keyboard = list[Button] | list[list[Button]]
type TotalKeyboard = list[list[Button]]
type KeyboardOrButton = Button | Keyboard

P = ParamSpec('P')
type CallableSignatures[R] = Callable[
    Concatenate[UIRegistry, UIContext, PropertiesUIContext],
    R | Awaitable[R],
]
type CallableAndValue[R] = CallableSignatures[R] | CallableWrapper[R] | R
type CallableValue[R] = CallableSignatures[R] | CallableWrapper[R]


@dataclass
class Button:
    """
    Готовый объект кнопки с уже переведенным именем, но не хэшированным callback.
    """

    id: str
    obj: InlineKeyboardButton


@dataclass
class Menu:
    """
    Объект меню.
    """

    text: CallableAndValue[str] | None = None
    image: CallableAndValue[str] | None = None
    upper_keyboard: CallableAndValue[Keyboard] | None = None
    keyboard: CallableAndValue[Keyboard] | None = None
    footer_keyboard: CallableAndValue[Keyboard] | None = None

    def __post_init__(self):
        self.text = (
            self.text
            if isinstance(self.text, str | None | CallableWrapper)
            else CallableWrapper(self.text)
        )
        self.image = (
            self.image
            if isinstance(self.image, str | None | CallableWrapper)
            else CallableWrapper(self.image)
        )

        u_k, k, f_k = [
            CallableWrapper(i) if not isinstance(i, list | CallableWrapper | None) else i
            for i in [self.upper_keyboard, self.keyboard, self.footer_keyboard]
        ]
        self.upper_keyboard, self.keyboard, self.footer_keyboard = u_k, k, f_k

    async def menu_text(
        self, ui: UIRegistry, ctx: UIContext | PropertiesUIContext, data: dict[str, Any]
    ) -> str | None:
        if isinstance(self.text, str | None):
            return self.text
        return await self.text((ui, ctx), data)

    async def menu_image(
        self, ui: UIRegistry, ctx: UIContext | PropertiesUIContext, data: dict[str, Any]
    ) -> str | None:
        if isinstance(self.image, str | None):
            return self.image
        return await self.image((ui, ctx), data)

    @overload
    async def total_keyboard(
        self,
        ui: UIRegistry,
        ctx: UIContext | PropertiesUIContext,
        data: dict[str, Any],
        convert: Literal[True],
    ) -> InlineKeyboardMarkup | None:
        pass

    @overload
    async def total_keyboard(
        self,
        ui: UIRegistry,
        ctx: UIContext | PropertiesUIContext,
        data: dict[str, Any],
        convert: Literal[False],
    ) -> TotalKeyboard | None:
        pass

    async def total_keyboard(
        self,
        ui: UIRegistry,
        ctx: UIContext | PropertiesUIContext,
        data: dict[str, Any],
        convert: bool = False,
    ) -> TotalKeyboard | InlineKeyboardMarkup | None:
        total_keyboard = []
        for kb in [self.upper_keyboard, self.keyboard, self.footer_keyboard]:
            if not kb:
                continue
            if not isinstance(kb, CallableWrapper):
                self._append_keyboard(kb, total_keyboard)
            else:
                to_append = await kb((ui, ctx), data)
                self._append_keyboard(to_append, total_keyboard)

        if not total_keyboard:
            return None

        return self.to_aiogram_keyboard(total_keyboard) if convert else total_keyboard

    def to_aiogram_keyboard(self, keyboard: TotalKeyboard) -> InlineKeyboardMarkup:
        aiogram_keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for line in keyboard:
            aiogram_keyboard.inline_keyboard.append([i.obj for i in line])
        return aiogram_keyboard

    def _append_keyboard(self, keyboard: Keyboard, total: TotalKeyboard) -> None:
        if not keyboard:
            return

        for i in keyboard:
            if isinstance(i, list):
                total.extend(keyboard)
                return
        total.append(keyboard)


@dataclass
class Window:
    """
    Итоговый объект меню после всех модификаций.
    """

    text: str | None = None
    image: str | None = None
    keyboard: Keyboard | None = None


@dataclass
class UIContext:
    translater: Translater
    language: str
    max_elements_on_page: int
    page: int
    current_callback: str
    callbacks_history: list[str]


@dataclass
class PropertiesUIContext(UIContext):
    entry: Properties | MutableParameter


@dataclass
class OneStepPropertiesUIBuilder:
    button_builder: CallableValue[Button]


@dataclass
class PropertiesUIBuilder(OneStepPropertiesUIBuilder):
    next_menu: CallableValue[Menu]
