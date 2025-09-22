from __future__ import annotations

import math
from typing import TYPE_CHECKING
from dataclasses import replace

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties import Parameter, ChoiceParameter
from funpayhub.lib.properties.flags import DefaultPropertiesFlags as Flags

from .types import Menu, Button, Keyboard, PropertiesUIContext
import html


if TYPE_CHECKING:
    from .registry import UIRegistry


# ToggleParameter
async def build_toggle_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError('')  # todo

    btn_callback = cbs.NextParamValue(path=ctx.entry.path).pack()
    total_callback = '->'.join([*ctx.callbacks_history, btn_callback])
    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    btn = InlineKeyboardButton(
        callback_data=total_callback,
        text=f'{"🟢" if ctx.entry.value else "🔴"} {translated_name}',
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


# Int / Float / String parameter
async def build_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError(f'{type(ctx.entry)} is not a Parameter.')

    btn_callback = cbs.ManualParamValueInput(path=ctx.entry.path).pack()
    total_callback = '->'.join([*ctx.callbacks_history, btn_callback])
    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    if Flags.PROTECT_VALUE not in ctx.entry._flags:
        val_str = (
            f'{str(ctx.entry.value)[:20] + ("..." if len(str(ctx.entry.value)) > 20 else "")}'
        )
    else:
        val_str = '••••••••'

    btn = InlineKeyboardButton(
        callback_data=total_callback,
        text=f'{translated_name} 【 {val_str} 】',
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


async def build_parameter_change_menu(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError('')

    text = ui.translater.translate('$enter_new_value_message', language=ctx.language).format(
        parameter_name=ui.translater.translate(ctx.entry.name, ctx.language),
        parameter_description=ui.translater.translate(ctx.entry.description, ctx.language),
        current_parameter_value=html.escape(str(ctx.entry.value)),
    )

    btn_callback = cbs.Clear().pack()
    total_callback = '->'.join([*ctx.callbacks_history, btn_callback])

    footer_keyboard = [
        Button(
            id='clear_state',
            obj=InlineKeyboardButton(
                text=ui.translater.translate('$clear_state', ctx.language),
                callback_data=total_callback,
            ),
        ),
    ]

    return Menu(text=text, footer_keyboard=footer_keyboard)


# List / Choice / Properties button
async def build_long_value_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    btn_callback = cbs.OpenPropertiesMenu(path=ctx.entry.path).pack()
    total_callback = '->'.join([*ctx.callbacks_history, btn_callback])
    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    btn = InlineKeyboardButton(
        callback_data=total_callback,
        text=translated_name,
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


# properties
async def build_properties_keyboard(ui: UIRegistry, ctx: PropertiesUIContext, **data) -> Keyboard:
    keyboard = []

    first_element = ctx.page * ctx.max_elements_on_page
    last_element = first_element + ctx.max_elements_on_page
    entries = list(ctx.entry.entries.items())[first_element:last_element]

    for entry_id, entry in entries:
        builder = ui.find_properties_btn_builder(type(entry))
        if not builder:
            continue

        btn_ctx = replace(
            ctx,
            page=0,
            callbacks_history=ctx.callbacks_history + [ctx.current_callback],
            entry=entry,
        )

        keyboard.append([await builder((ui, btn_ctx), data=data)])
    return keyboard


async def build_choice_parameter_keyboard(ui: UIRegistry, ctx: PropertiesUIContext, **data) -> Keyboard:
    if not isinstance(ctx.entry, ChoiceParameter):
        raise ValueError(f'{type(ctx.entry)} is not a `ChoiceParameter`.')
    keyboard = []
    first_element = ctx.page * ctx.max_elements_on_page
    last_element = first_element + ctx.max_elements_on_page
    choices = list(ctx.entry.choices)[first_element:last_element]

    for index, choice in enumerate(choices):
        cb = cbs.ChooseParamValue(
            path=ctx.entry.path,
            choice_index=index+first_element
        ).pack()
        cb = '->'.join([*ctx.callbacks_history, ctx.current_callback, cb])

        name = ui.translater.translate(choice.name, ctx.language)
        text = f'【 {name} 】' if ctx.entry.value == index+first_element else name

        btn = InlineKeyboardButton(
            text=text,
            callback_data=cb
        )
        keyboard.append([
            Button(
                id=f'choice_param_value:{index+first_element}:{ctx.entry.path}',
                obj=btn
            )
        ])
    return keyboard


async def build_properties_footer(ui: UIRegistry, ctx: PropertiesUIContext) -> Keyboard:
    total_pages = math.ceil(len(ctx.entry) / ctx.max_elements_on_page)
    new_history = ctx.callbacks_history + [ctx.current_callback]

    kb = []

    if ctx.callbacks_history:
        back_btn = InlineKeyboardButton(
            text=ui.translater.translate('$back', ctx.language),
            callback_data='->'.join(ctx.callbacks_history),
        )
        kb.append(
            [
                Button(id='back', obj=back_btn),
            ],
        )

    if total_pages < 2:
        return kb

    page_amount_cb = (
        cbs.ChangePageManually(total_pages=total_pages).pack()
        if total_pages > 1
        else cbs.Dummy().pack()
    )

    page_amount_cb = '->'.join([*new_history, page_amount_cb])

    page_amount_btn = InlineKeyboardButton(
        text=f'{ctx.page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=page_amount_cb,
    )

    to_first_cb = cbs.ChangePageTo(page=0).pack() if ctx.page > 0 else cbs.Dummy().pack()
    to_first_cb = '->'.join([*new_history, to_first_cb])

    to_first_btn = InlineKeyboardButton(
        text='⏪' if ctx.page > 0 else '❌',
        callback_data=to_first_cb,
    )

    to_last_cb = (
        cbs.ChangePageTo(page=total_pages - 1).pack()
        if ctx.page < total_pages - 1
        else cbs.Dummy().pack()
    )
    to_last_cb = '->'.join([*new_history, to_last_cb])

    to_last_btn = InlineKeyboardButton(
        text='⏩' if ctx.page < total_pages - 1 else '❌',
        callback_data=to_last_cb,
    )

    to_previous_cb = (
        cbs.ChangePageTo(page=ctx.page - 1).pack() if ctx.page > 0 else cbs.Dummy().pack()
    )
    to_previous_cb = '->'.join([*new_history, to_previous_cb])
    to_previous_btn = InlineKeyboardButton(
        text='◀️' if ctx.page > 0 else '❌',
        callback_data=to_previous_cb,
    )

    to_next_cb = (
        cbs.ChangePageTo(page=ctx.page + 1).pack()
        if ctx.page < total_pages - 1
        else cbs.Dummy().pack()
    )
    to_next_cb = '->'.join([*new_history, to_next_cb])

    to_next_btn = InlineKeyboardButton(
        text='▶️' if ctx.page < total_pages - 1 else '❌',
        callback_data=to_next_cb,
    )

    kb.insert(
        0,
        [
            Button(id='to_first_page', obj=to_first_btn),
            Button(id='to_previous_page', obj=to_previous_btn),
            Button(id='page_counter', obj=page_amount_btn),
            Button(id='to_next_page', obj=to_next_btn),
            Button(id='to_last_page', obj=to_last_btn),
        ],
    )

    return kb


async def build_properties_text(ui: UIRegistry, ctx: PropertiesUIContext) -> str:
    return f"""<u><b>{ui.translater.translate(ctx.entry.name, ctx.language)}</b></u>

<i>{ui.translater.translate(ctx.entry.description, ctx.language)}</i>
"""


async def properties_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    return Menu(
        text=build_properties_text,
        image=None,
        upper_keyboard=None,
        keyboard=build_properties_keyboard,
        footer_keyboard=build_properties_footer,
    )


async def choice_parameter_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    return Menu(
        text=build_properties_text,
        image=None,
        upper_keyboard=None,
        keyboard=build_choice_parameter_keyboard,
        footer_keyboard=build_properties_footer,
    )
