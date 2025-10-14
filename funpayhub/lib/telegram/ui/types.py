from __future__ import annotations


__all__ = [
    'Keyboard',
    'Button',
    'Menu',
    'UIContext',
]

from typing import TYPE_CHECKING, Literal, Optional, Concatenate, overload, Any
from dataclasses import dataclass, field
from collections.abc import Callable, Awaitable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from funpayhub.lib.telegram.callback_data import UnknownCallback
from aiogram.types import Message


if TYPE_CHECKING:
    from .registry import UIRegistry


type Keyboard = list[list[Button]]
type Finalizer[**P] = (
    Callable[
        Concatenate[UIRegistry, UIContext, Menu, P],
        Menu | Awaitable[Menu],
    ]
    | None
)


@dataclass
class Button:
    button_id: str
    obj: InlineKeyboardButton


@dataclass
class Menu:
    """
    Объект меню.
    """

    ui: UIRegistry
    context: UIContext

    text: str = None
    image: Optional[str] = None
    header_keyboard: Keyboard = field(default_factory=list)
    keyboard: Keyboard = field(default_factory=list)
    footer_keyboard: Keyboard = field(default_factory=list)
    finalizer: Finalizer = None

    @overload
    def total_keyboard(self, convert: Literal[True]) -> InlineKeyboardMarkup | None: pass

    @overload
    def total_keyboard(self, convert: Literal[False]) -> Keyboard | None: pass

    def total_keyboard(
        self,
        convert: bool = False,
    ) -> Keyboard | InlineKeyboardMarkup | None:
        total_keyboard = [*self.header_keyboard, *self.keyboard, *self.footer_keyboard]
        if not total_keyboard:
            return None
        if not convert:
            return total_keyboard

        for line_index, line in enumerate(total_keyboard):
            for button_index, button in enumerate(line):
                total_keyboard[line_index][button_index] = button.obj
        return total_keyboard

    async def reply_to(self, message: Message) -> Message:
        return await message.answer(
            text=self.text,
            reply_markup=self.total_keyboard(convert=True),
        )

    async def apply_to(self, message: Message):
        return await message.edit_text(
            text=self.text,
            reply_markup=self.total_keyboard(convert=True),
        )


@dataclass(kw_only=True)
class UIContext:
    language: str
    max_elements_on_page: int
    menu_page: int = 0
    view_page: int = 0
    callback: UnknownCallback
