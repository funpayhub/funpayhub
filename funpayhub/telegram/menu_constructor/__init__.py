from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardButton
from funpayhub.properties import Parameter, MutableParameter, Properties, ToggleParameter, StringParameter, \
    IntParameter, FloatParameter, ChoiceParameter
import math

from ..app import callbacks as cbs


class PropertiesMenu:
    def __init__(self, properties: Properties, max_entries_on_page: int = 6) -> None:
        self.properties = properties
        self.max_entries_on_page = max_entries_on_page

    def build_menu(self, page_index: int) -> InlineKeyboardMarkup:
        start_point = page_index * self.max_entries_on_page
        end_point = start_point + self.max_entries_on_page

        entries = list(self.properties.entries.items())[start_point:end_point]

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
                    callback_data=cbs.ToggleParameter(path=obj.path, opened_props_page=page_index).pack()
                ))

            elif isinstance(obj, ChoiceParameter):
                builder.row(InlineKeyboardButton(
                    text=f'{obj.name}',
                    callback_data=cbs.OpenProperties(path=obj.path).pack()
                ))

            elif isinstance(obj, StringParameter | IntParameter | FloatParameter):
                builder.row(InlineKeyboardButton(
                    text=f'{obj.name}',
                    callback_data=cbs.ChangeParameter(path=obj.path, opened_props_page=page_index).pack()
                ))

        self.build_footer(builder, page_index)
        return builder.as_markup()

    def build_footer(self, builder: InlineKeyboardBuilder, page_index: int) -> None:
        total = len(self.properties.entries)
        pages_amount = math.ceil(total / self.max_entries_on_page)

        if pages_amount > 1:


            page_amount_btn = InlineKeyboardButton(
                text=f'{page_index+1}/{pages_amount}',
                callback_data=f'dummy'
            )
            to_first_btn = InlineKeyboardButton(
                text='⏮️',
                callback_data='dummy' if page_index == 0 else cbs.OpenProperties(path=self.properties.path, page=0).pack()
            )

            back_btn = InlineKeyboardButton(
                text='◀️',
                callback_data='dummy' if page_index == 0 else cbs.OpenProperties(path=self.properties.path, page=page_index-1).pack()
            )

            to_last_btn = InlineKeyboardButton(
                text='⏭️',
                callback_data='dummy' if page_index == (pages_amount-1) else cbs.OpenProperties(
                    path=self.properties.path, page=pages_amount-1).pack()
            )

            next_btn = InlineKeyboardButton(
                text='▶️',
                callback_data='dummy' if page_index == (pages_amount-1) else cbs.OpenProperties(
                    path=self.properties.path, page=page_index + 1).pack()
            )

            builder.row(to_first_btn, back_btn, page_amount_btn, next_btn, to_last_btn)

        if self.properties.parent:
            builder.row(
                InlineKeyboardButton(
                    text='◀️ ' + self.properties.parent.name,
                    callback_data = cbs.OpenProperties(path=self.properties.parent.path, page=0).pack()
                )
            )
