from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, TypeVar, Protocol
from copy import copy

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties import Properties, ChoiceParameter, ToggleParameter, MutableParameter


if TYPE_CHECKING:
    from .types import PropertiesMenuRenderContext


T = TypeVar('T', bound=Any)


class HasPageField(Protocol):
    page: int

    def pack(self) -> str: ...


def props_message_builder(ctx: PropertiesMenuRenderContext) -> str:
    return f'<b><u>{ctx.properties.name}</u></b>\n\n<i>{ctx.properties.description}</i>'


def props_menu_builder(ctx: PropertiesMenuRenderContext) -> InlineKeyboardMarkup:
    start_point = ctx.page_index * ctx.max_elements_on_page
    end_point = start_point + ctx.max_elements_on_page

    entries = list(ctx.properties.entries.items())[start_point:end_point]

    builder = InlineKeyboardBuilder()
    for id, obj in entries:
        if isinstance(obj, Properties):
            builder.row(
                InlineKeyboardButton(
                    text=obj.name,
                    callback_data=cbs.OpenProperties(path=obj.path).pack(),
                )
            )

        elif isinstance(obj, ToggleParameter):
            builder.row(
                InlineKeyboardButton(
                    text=f'{"🟢" if obj.value else "🔴"} {obj.name}',
                    callback_data=cbs.ToggleParameter(path=obj.path, page=ctx.page_index).pack(),
                )
            )

        elif isinstance(obj, ChoiceParameter):
            builder.row(
                InlineKeyboardButton(
                    text=f'{obj.name}',
                    callback_data=cbs.OpenChoiceParameter(path=obj.path).pack(),
                )
            )

        elif isinstance(obj, MutableParameter):
            builder.row(
                InlineKeyboardButton(
                    text=f'{obj.name}',
                    callback_data=cbs.ChangeParameter(path=obj.path, page=ctx.page_index).pack(),
                )
            )
    return builder.as_markup()


def props_menu_header_builder(ctx: PropertiesMenuRenderContext) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])


def _set(obj: T, key: str, value: Any) -> T:
    setattr(obj, key, value)
    return obj


def footer_builder(
    page_index: int,
    pages_amount: int,
    page_callback: HasPageField,
) -> InlineKeyboardMarkup:
    if pages_amount < 2:
        return InlineKeyboardMarkup(inline_keyboard=[])

    builder = InlineKeyboardBuilder()
    page_amount_btn = InlineKeyboardButton(
        text=f'{page_index + (1 if pages_amount else 0)}/{pages_amount}',
        callback_data=cbs.SelectPage(query=page_callback.pack()).pack(),
    )

    to_first_btn = InlineKeyboardButton(
        text='⏮️',
        callback_data=cbs.Dummy().pack()
        if not page_index
        else _set(
            copy(page_callback),
            'page',
            0,
        ).pack(),
    )

    back_btn = InlineKeyboardButton(
        text='◀️',
        callback_data=cbs.Dummy().pack()
        if not page_index
        else _set(
            copy(page_callback),
            'page',
            page_index - 1,
        ).pack(),
    )

    to_last_btn = InlineKeyboardButton(
        text='⏭️',
        callback_data=cbs.Dummy().pack()
        if page_index == (pages_amount - 1)
        else _set(
            copy(page_callback),
            'page',
            pages_amount - 1,
        ).pack(),
    )

    next_btn = InlineKeyboardButton(
        text='▶️',
        callback_data=cbs.Dummy().pack()
        if page_index == (pages_amount - 1)
        else _set(
            copy(page_callback),
            'page',
            page_index + 1,
        ).pack(),
    )

    builder.row(to_first_btn, back_btn, page_amount_btn, next_btn, to_last_btn)
    return builder.as_markup()


def props_footer_builder(ctx: PropertiesMenuRenderContext) -> InlineKeyboardMarkup:
    entries_amount = len(ctx.properties.entries)
    footer = footer_builder(
        page_index=ctx.page_index,
        pages_amount=math.ceil(entries_amount / ctx.max_elements_on_page),
        page_callback=cbs.OpenProperties(path=ctx.properties.path),
    )
    if ctx.properties.parent:
        footer.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f'◀️ {ctx.properties.parent.name}',
                    callback_data=cbs.OpenProperties(path=ctx.properties.parent.path).pack(),
                ),
            ],
        )
    return footer
