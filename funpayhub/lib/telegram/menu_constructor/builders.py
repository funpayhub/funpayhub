from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import funpayhub.lib.telegram.callbacks as cbs
from copy import copy
import math
from typing import TypeVar, Any, Protocol
from funpayhub.lib.properties import Properties, ToggleParameter, ChoiceParameter, MutableParameter


T = TypeVar("T", bound=Any)


class HasPageField(Protocol):
    page: int

    def pack(self) -> str: ...


def props_message_builder(props: Properties, page_index: int, elements_on_page: int) -> str:
    return f'<b><u>{props.name}</u></b>\n\n<i>{props.description}</i>'


def props_menu_builder(props: Properties, page_index: int, elements_on_page: int) -> InlineKeyboardMarkup:
    start_point = page_index * elements_on_page
    end_point = start_point + elements_on_page

    entries = list(props.entries.items())[start_point:end_point]

    builder = InlineKeyboardBuilder()
    for id, obj in entries:
        if isinstance(obj, Properties):
            builder.row(InlineKeyboardButton(
                text=obj.name,
                callback_data=cbs.OpenProperties(path=obj.path).pack()
            ))

        elif isinstance(obj, ToggleParameter):
            builder.row(InlineKeyboardButton(
                text=f'{"🟢" if obj.value else "🔴"} {obj.name}',
                callback_data=cbs.ToggleParameter(path=obj.path, page=page_index).pack()
            ))

        elif isinstance(obj, ChoiceParameter):
            builder.row(InlineKeyboardButton(
                text=f'{obj.name}',
                callback_data=cbs.OpenChoiceParameter(path=obj.path).pack()
            ))

        elif isinstance(obj, MutableParameter):
            builder.row(InlineKeyboardButton(
                text=f'{obj.name}',
                callback_data=cbs.ChangeParameter(path=obj.path, page=page_index).pack()
            ))
    return builder.as_markup()


def props_menu_header_builder(props: Properties, page_index: int, elements_on_page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])


def _set(obj: T, key: str, value: Any) -> T:
    setattr(obj, key, value)
    return obj


def footer_builder(
    page_index: int,
    pages_amount: int,
    page_callback: HasPageField
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    page_amount_btn = InlineKeyboardButton(
        text=f'{page_index + (1 if pages_amount else 0)}/{pages_amount}',
        callback_data=cbs.Dummy().pack()
    )

    to_first_btn = InlineKeyboardButton(
        text='⏮️',
        callback_data=cbs.Dummy().pack() if not page_index else _set(
            copy(page_callback),
            'page',
            0
        ).pack()
    )

    back_btn = InlineKeyboardButton(
        text='◀️',
        callback_data=cbs.Dummy().pack() if not page_index else _set(
            copy(page_callback),
            'page',
            page_index-1
        ).pack()
    )

    to_last_btn = InlineKeyboardButton(
        text='⏭️',
        callback_data=cbs.Dummy().pack() if page_index == (pages_amount - 1) else _set(
            copy(page_callback),
            'page',
            pages_amount-1
        ).pack()

    )

    next_btn = InlineKeyboardButton(
        text='▶️',
        callback_data=cbs.Dummy().pack() if page_index == (pages_amount - 1) else _set(
            copy(page_callback),
            'page',
            page_index+1
        ).pack()
    )

    builder.row(to_first_btn, back_btn, page_amount_btn, next_btn, to_last_btn)

    return builder.as_markup()


def props_footer_builder(props: Properties, page_index: int, elements_on_page_amount: int) -> InlineKeyboardMarkup:
    entries_amount = len(props.entries)
    footer = footer_builder(
        page_index=page_index,
        pages_amount=math.ceil(entries_amount / elements_on_page_amount),
        page_callback=cbs.OpenProperties(path=props.path)
    )
    if props.parent:
        p = props.parent
        footer.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f'◀️ {p.name}',
                    callback_data=cbs.OpenProperties(path=p.path).pack()
                )
            ]
        )
    return footer
