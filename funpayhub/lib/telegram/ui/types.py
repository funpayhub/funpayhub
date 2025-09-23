from __future__ import annotations


__all__ = [
    'Keyboard',
    'Button',
    'Menu',
    'UIContext',
    'PropertiesUIContext',
]


from typing import TYPE_CHECKING, Any, Literal, Optional, ParamSpec, Concatenate, overload
from dataclasses import field, dataclass
from collections.abc import Callable, Awaitable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.telegram.callbacks import Hash


if TYPE_CHECKING:
    from .registry import UIRegistry


type Keyboard = list[list[Button]]
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
    Готовая кнопка пропущенная через переводчик, но не через хэшинатор.
    """

    id: str
    """ID кнопки."""

    obj: InlineKeyboardButton
    """Объект Aiogram кнопки."""


@dataclass
class Menu:
    """
    Объект меню.
    """

    ui: UIRegistry
    context: UIContext

    text: Optional[str] = None
    image: Optional[str] = None
    upper_keyboard: Optional[Keyboard] = None
    keyboard: Optional[Keyboard] = None
    footer_keyboard: Optional[Keyboard] = None

    @overload
    def total_keyboard(
        self,
        convert: Literal[True],
        hash: bool = True,
    ) -> InlineKeyboardMarkup | None:
        pass

    @overload
    def total_keyboard(
        self,
        convert: Literal[False],
        hash: bool = True,
    ) -> Keyboard | None:
        pass

    def total_keyboard(
        self,
        convert: bool = False,
        hash: bool = True,
    ) -> Keyboard | InlineKeyboardMarkup | None:
        total_keyboard = []
        for kb in [self.upper_keyboard, self.keyboard, self.footer_keyboard]:
            if not kb:
                continue
            for line in kb:
                converted_line = []
                for button in line:
                    if button.obj.callback_data and hash:
                        button.obj.callback_data = Hash(
                            hash=self.ui.hashinator.hash(button.obj.callback_data),
                        ).pack()
                    converted_line.append(button.obj if convert else button)
                total_keyboard.append(converted_line)

        if not total_keyboard:
            return None
        if convert:
            return InlineKeyboardMarkup(inline_keyboard=total_keyboard)
        return total_keyboard


@dataclass(kw_only=True)
class UIContext:
    language: str
    max_elements_on_page: int
    page: int
    current_callback: str
    callbacks_history: list[str]
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class PropertiesUIContext(UIContext):
    entry: Properties | MutableParameter
