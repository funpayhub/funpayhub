from __future__ import annotations


__all__ = [
    'Keyboard',
    'Button',
    'Menu',
    'UIContext',
    'PropertiesUIContext',
]

from typing import TYPE_CHECKING, Literal, Optional, Concatenate, overload
from dataclasses import dataclass, field
from collections.abc import Callable, Awaitable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.telegram.callbacks import Hash
from funpayhub.lib.telegram.callback_data import UnknownCallback
from aiogram.types import Message


if TYPE_CHECKING:
    from .registry import UIRegistry


type Keyboard = list[list[Button]]
type Finalizer[**P] = (
    Callable[
        Concatenate[UIRegistry, UIContext | PropertiesUIContext, Menu, P],
        Menu | Awaitable[Menu],
    ]
    | None
)


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
    header_keyboard: Optional[Keyboard] = field(default_factory=list)
    keyboard: Optional[Keyboard] = field(default_factory=list)
    footer_keyboard: Optional[Keyboard] = field(default_factory=list)
    finalizer: Finalizer = None

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
        for kb in [self.header_keyboard, self.keyboard, self.footer_keyboard]:
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

    async def reply_to(self, message: Message, hash: bool = True) -> Message:
        return await message.answer(
            text=self.text,
            reply_markup=self.total_keyboard(convert=True, hash=hash),
        )

    async def apply_to(self, message: Message, hash: bool = True):
        return await message.edit_text(
            text=self.text,
            reply_markup=self.total_keyboard(convert=True, hash=hash),
        )


@dataclass(kw_only=True)
class UIContext:
    language: str
    max_elements_on_page: int
    menu_page: int = 0
    view_page: int = 0
    callback: UnknownCallback


@dataclass(kw_only=True)
class PropertiesUIContext(UIContext):
    entry: Properties | MutableParameter
