from __future__ import annotations

from dataclasses import dataclass, field
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, Chat, ChatFullInfo, User, \
    CallbackQuery
from typing import Literal, overload, Any


type Keyboard = list[list[Button]]


@dataclass
class Button:
    button_id: str
    obj: InlineKeyboardButton


@dataclass
class Menu:
    text: str = ''
    image: str | None = None
    header_keyboard: Keyboard = field(default_factory=list)
    main_keyboard: Keyboard = field(default_factory=list)
    footer_keyboard: Keyboard = field(default_factory=list)

    @overload
    def total_keyboard(self, convert: Literal[True]) -> InlineKeyboardMarkup | None:
        pass

    @overload
    def total_keyboard(self, convert: Literal[False]) -> Keyboard | None:
        pass

    def total_keyboard(self, convert: bool = False) -> Keyboard | InlineKeyboardMarkup | None:
        total_keyboard = [*self.header_keyboard, *self.main_keyboard, *self.footer_keyboard]
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

    async def apply_to(self, message: Message) -> Message | bool:
        return await message.edit_text(
            text=self.text,
            reply_markup=self.total_keyboard(convert=True),
        )


@dataclass(kw_only=True, frozen=True)
class UIRenderContext:
    language: str
    max_lines: int
    menu_page: int = 0
    view_page: int = 0
    chat: Chat | ChatFullInfo
    thread_id: int | None = None
    message_id: int | None = None
    trigger: Message | CallbackQuery | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        language: str,
        max_lines: int,
        menu_page: int,
        view_page: int,
        **kwargs: Any
    ) -> UIRenderContext:
        return UIRenderContext(
            language=language,
            max_lines=max_lines,
            menu_page=menu_page,
            view_page=view_page,
            data=kwargs
        )