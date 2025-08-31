from dataclasses import dataclass
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import TYPE_CHECKING, Protocol, Any, TypeVar, Awaitable, Callable
from ..app.callbacks import Dummy
from copy import copy

if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties
    from aiogram.filters.callback_data import CallbackData


T = TypeVar('T', bound=Any)


class HasPageField(Protocol):
    page: int

    def pack(self) -> str: ...


class TelegramMenuRenderer:
    def __init__(self):
        self.modifiers = {}


@dataclass
class PropertiesTelegramMenu:
    message: Callable[..., str | Awaitable[str]] | str
    keyboard: Callable[..., InlineKeyboardBuilder | Awaitable[InlineKeyboardBuilder]] | InlineKeyboardBuilder
    header: Callable[..., InlineKeyboardBuilder | Awaitable[InlineKeyboardBuilder]] | InlineKeyboardBuilder
    footer: Callable[..., InlineKeyboardBuilder | Awaitable[InlineKeyboardBuilder]] | InlineKeyboardBuilder


def props_telegram_keyboard(props: Properties) -> ...:
    message = f"<b>{props.name}</b>\n\n<i>{props.description}</i>"

    return TelegramMenu(
        message=message,
    )


def _set(obj: T, key: str, value: Any) -> T:
    setattr(obj, key, value)
    return obj


def footer_builder(
    page_index: int,
    pages_amount: int,
    page_callback: HasPageField
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    page_amount_btn = InlineKeyboardButton(
        text=f'{page_index + (1 if pages_amount else 0)}/{pages_amount}',
        callback_data=Dummy().pack()
    )

    to_first_btn = InlineKeyboardButton(
        text='⏮️',
        callback_data=Dummy().pack() if not page_index else _set(
            copy(page_callback),
            'page',
            0
        ).pack()
    )

    back_btn = InlineKeyboardButton(
        text='◀️',
        callback_data=Dummy().pack() if not page_index else _set(
            copy(page_callback),
            'page',
            page_index-1
        ).pack()
    )

    to_last_btn = InlineKeyboardButton(
        text='⏭️',
        callback_data=Dummy().pack() if page_index == (pages_amount - 1) else _set(
            copy(page_callback),
            'page',
            pages_amount-1
        ).pack()

    )

    next_btn = InlineKeyboardButton(
        text='▶️',
        callback_data=Dummy().pack() if page_index == (pages_amount - 1) else _set(
            copy(page_callback),
            'page',
            page_index+1
        ).pack()
    )

    builder.row(to_first_btn, back_btn, page_amount_btn, next_btn, to_last_btn)

    return builder
