from __future__ import annotations

from dataclasses import dataclass, field
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, Chat, ChatFullInfo, User, \
    CallbackQuery
from typing import Literal, overload, Any, Protocol


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
    menu_id: str
    menu_page: int = 0
    view_page: int = 0
    chat_id: int
    thread_id: int | None = None
    message_id: int | None = None
    trigger: Message | CallbackQuery | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        menu_id: str,
        menu_page: int,
        view_page: int,
        chat_id: int | None = None,
        thread_id: int | None = None,
        message_id: int | None = None,
        trigger: Message | CallbackQuery | None = None,
        **kwargs: Any
    ) -> UIRenderContext:
        if trigger is not None:
            msg = trigger if isinstance(trigger, Message) else trigger.message
            message_id, chat_id, thread_id = msg.message_id, msg.chat.id, msg.message_thread_id

        if chat_id is None:
            raise ValueError('Chat ID or trigger must be provided.')

        return UIRenderContext(
            menu_id=menu_id,
            menu_page=menu_page,
            view_page=view_page,
            chat_id=chat_id,
            thread_id=thread_id,
            message_id=message_id,
            trigger=trigger,
            data=kwargs
        )
