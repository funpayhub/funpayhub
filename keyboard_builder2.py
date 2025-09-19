from __future__ import annotations


from dataclasses import dataclass
import funpayhub.lib.properties.parameter as p
from typing import TYPE_CHECKING
from collections.abc import Callable, Awaitable
if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties, MutableParameter


@dataclass
class InPlaceChangeButtonBuilderContext:
    parameter: MutableParameter
    properties_page_index: int
    builder: KeyboardBuilder


@dataclass
class InPlaceChangeButtonBuilder:
    builder: Callable[[InPlaceChangeButtonBuilderContext], Awaitable[InlineKeyboardButton]]

    async def build(self, context: InPlaceChangeButtonBuilderContext) -> InlineKeyboardButton:
        return await self.builder(context)


@dataclass
class ManualChangeButtonBuilderContext:
    parameter: MutableParameter
    properties_page_index: int
    builder: KeyboardBuilder


@dataclass
class ManualChangeButtonBuilder:
    button_builder: Callable[[ManualChangeButtonBuilderContext], Awaitable[InlineKeyboardButton]]
    change_message_text_builder: Callable[[ManualChangeButtonBuilderContext], Awaitable[str]]
    change_message_keyboard_builder: Callable[[ManualChangeButtonBuilderContext], Awaitable[InlineKeyboardMarkup]]


@dataclass
class MenuChangeButtonBuilder:
    buttons: list[ManualChangeButtonBuilder]


@dataclass
class PropertiesMenuRenderContext:
    properties: Properties
    page_index: int
    max_elements_on_page: int
    builder: KeyboardBuilder


class KeyboardBuilder:
    def __init__(self):
        self.default = {
        p.ToggleParameter: InPlaceChangeButtonBuilder(build_toggle_keyboard),
        p.IntParameter: ManualChangeButtonBuilder('some_text'),
        p.FloatParameter: ManualChangeButtonBuilder('some_text'),
        p.StringParameter: ManualChangeButtonBuilder('some_text'),
        p.ListParameter: MenuChangeButtonBuilder([]),
        p.ChoiceParameter: MenuChangeButtonBuilder([])
    }

    def make_context(self, properties: Properties, page_index: int, max_elements_on_page: int) -> PropertiesMenuRenderContext:
        return PropertiesMenuRenderContext(
            properties=properties,
            page_index=page_index,
            max_elements_on_page=max_elements_on_page,
            builder=self
        )


from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup
import funpayhub.lib.telegram.callbacks as cbs


async def build_properties_keyboard(ctx: PropertiesMenuRenderContext) -> InlineKeyboardMarkup:
    result = []
    for entry_id, obj in ctx.properties.entries.items():
        if type(obj) not in ctx.builder.default:
            continue

        builder = ctx.builder.default[type(obj)]
        if isinstance(builder, InPlaceChangeButtonBuilder):
            context = InPlaceChangeButtonBuilderContext(
                parameter=obj,
                properties_page_index=ctx.page_index,
                builder=ctx.builder
            )
            result.append(await builder.build(context))

        elif isinstance(builder, ManualChangeButtonBuilder):
            ...

        elif isinstance(builder, MenuChangeButtonBuilder):
            ...


async def build_toggle_keyboard(ctx: InPlaceChangeButtonBuilderContext) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=f'{"🟢" if ctx.parameter.value else "🔴"} {ctx.parameter.name}',
        callback_data=cbs.ToggleParameter(path=ctx.parameter.path, page=ctx.properties_page_index).pack(),
    )


async def build_manual_change_button(ctx: ManualChangeButtonBuilderContext) -> InlineKeyboardButton:
    val_str = f'{str(ctx.parameter.value)[:20] + ("..." if len(str(ctx.parameter.value)) > 20 else "")}'
    return InlineKeyboardButton(
        text=f'{ctx.parameter.name} 【 {val_str} 】',
        callback_data=cbs.ChangeParameter(path=ctx.parameter.path, page=ctx.properties_page_index).pack(),
    )


async def build_message_keyboard(ctx: ManualChangeButtonBuilderContext) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='$clear_state', )]
        ]
    )