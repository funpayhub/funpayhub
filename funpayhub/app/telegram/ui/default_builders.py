from __future__ import annotations

import html
import math
from typing import TYPE_CHECKING
from dataclasses import replace

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.loggers import tg_ui_logger as logger
from funpayhub.lib.properties import Parameter, ChoiceParameter, ToggleParameter
from funpayhub.lib.telegram.callbacks_parsing import join_callbacks, add_callback_params
from funpayhub.lib.properties.flags import DefaultPropertiesFlags as Flags
from funpayhub.lib.telegram.ui.types import RenderedMenu, Button, Keyboard, PropertiesUIContext, UIContext
from funpayhub.lib.hub.text_formatters import FormattersRegistry

from . import button_ids as ids
from . import premade


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


# ToggleParameter
async def build_toggle_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    """
    Дефолтный билдер кнопки параметра-переключателя.

    Использует коллбэк `NextParamValue`.
    """
    logger.debug(f'Building toggle parameter button for {ctx.entry.path}')

    if not isinstance(ctx.entry, ToggleParameter):
        raise ValueError(f'{type(ctx.entry)} is not a ToggleParameter.')

    btn_callback = cbs.NextParamValue(path=ctx.entry.path).pack()
    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    btn = InlineKeyboardButton(
        callback_data=join_callbacks(ctx.callback.pack(), btn_callback),
        text=f'{"🟢" if ctx.entry.value else "🔴"} {translated_name}',
    )

    return Button(id=f'{ids.TOGGLE_PARAM_BTN}:{ctx.entry.path}', obj=btn)


# Int / Float / String parameter
async def build_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    """
    Дефолтный билдер для кнопки параметра с ручным вводом значения (через сообщение).

    Отображает значение параметра (первые 20 символов) в 【 скобках 】.

    Если у параметра есть флаг `PROTECT_VALUE`, отображает значение в виде `••••••••`.

    Использует коллбэк `ManualParamValueInput`.
    """

    logger.debug(f'Building default parameter button for {ctx.entry.path}')

    if not isinstance(ctx.entry, Parameter):
        raise ValueError(f'{type(ctx.entry)} is not a Parameter.')

    btn_callback = cbs.ManualParamValueInput(path=ctx.entry.path).pack()
    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    if Flags.PROTECT_VALUE not in ctx.entry._flags:
        val_str = (
            f'{str(ctx.entry.value)[:20] + ("..." if len(str(ctx.entry.value)) > 20 else "")}'
        )
    else:
        val_str = '•' * 8

    btn = InlineKeyboardButton(
        callback_data=join_callbacks(ctx.callback.pack(), btn_callback),
        text=f'{translated_name} 【 {val_str} 】',
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


# List / Choice / Properties button
async def build_open_menu_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    """
    Дефолтный билдер для кнопки открытия меню параметра / категории параметров.

    Использует коллбэк `OpenEntryMenu`.
    """
    btn_callback = cbs.OpenEntryMenu(path=ctx.entry.path).pack()
    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    btn = InlineKeyboardButton(
        callback_data=join_callbacks(ctx.callback.pack(), btn_callback),
        text=translated_name,
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


# Properties keyboard
async def build_properties_keyboard(ui: UIRegistry, ctx: PropertiesUIContext, **data) -> Keyboard:
    keyboard = []

    for entry_id, entry in ctx.entry.entries.items():
        builder = ui.find_properties_btn_builder(type(entry))
        if not builder:
            continue

        btn_ctx = replace(
            ctx,
            page=0,
            entry=entry,
        )

        keyboard.append([await builder((ui, btn_ctx), data=data)])
    return keyboard


# Choice parameter keyboard
async def build_choice_parameter_keyboard(ui: UIRegistry, ctx: PropertiesUIContext) -> Keyboard:
    if not isinstance(ctx.entry, ChoiceParameter):
        raise ValueError(f'{type(ctx.entry)} is not a `ChoiceParameter`.')

    keyboard = []

    for index, choice in enumerate(ctx.entry.choices):
        cb = cbs.ChooseParamValue(path=ctx.entry.path, choice_index=index).pack()
        name = ui.translater.translate(choice.name, ctx.language)

        btn = InlineKeyboardButton(
            text=f'【 {name} 】' if ctx.entry.value == index else name,
            callback_data=join_callbacks(ctx.callback.pack(), cb),
        )
        keyboard.append(
            [
                Button(
                    id=f'choice_param_value:{index}:{ctx.entry.path}',
                    obj=btn,
                ),
            ],
        )
    return keyboard


async def build_parameter_change_menu(ui: UIRegistry, ctx: PropertiesUIContext) -> RenderedMenu:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError('')

    text = ui.translater.translate('$enter_new_value_message', language=ctx.language).format(
        parameter_name=ui.translater.translate(ctx.entry.name, ctx.language),
        parameter_description=ui.translater.translate(ctx.entry.description, ctx.language),
        current_parameter_value=html.escape(str(ctx.entry.value)),
    )

    footer_keyboard = [
        Button(
            id='clear_state',
            obj=InlineKeyboardButton(
                text=ui.translater.translate('$clear_state', ctx.language),
                callback_data=join_callbacks(*ctx.callback.history, cbs.Clear().pack()),
            ),
        ),
    ]

    return RenderedMenu(
        ui=ui,
        context=ctx,
        text=text,
        footer_keyboard=[footer_keyboard],
    )


async def build_properties_text(ui: UIRegistry, ctx: PropertiesUIContext) -> str:
    return f"""<u><b>{ui.translater.translate(ctx.entry.name, ctx.language)}</b></u>

<i>{ui.translater.translate(ctx.entry.description, ctx.language)}</i>
"""

# Formatters
async def build_formatters_keyboard(ui: UIRegistry, ctx: UIContext, fp_formatters: FormattersRegistry) -> Keyboard:
    keyboard = []
    for formatter in fp_formatters:
        cb = cbs.OpenMenu(menu_id='fph-formatter-info').pack()
        cb = add_callback_params(cb, formatter_id=formatter.key)

        btn = InlineKeyboardButton(
            text=ui.translater.translate(formatter.name, ctx.language),
            callback_data=join_callbacks(ctx.callback.pack(), cb),
        )
        keyboard.append([Button(id=f'open_formatter_info:{formatter.key}', obj=btn)])
    return keyboard


async def properties_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext, **data) -> RenderedMenu:
    total_pages = math.ceil(len(ctx.entry.entries) / ctx.max_elements_on_page)

    return RenderedMenu(
        ui=ui,
        context=ctx,
        text=await build_properties_text(ui, ctx),
        image=None,
        upper_keyboard=None,
        keyboard=await build_properties_keyboard(ui, ctx, **data),
        footer_keyboard=await premade.build_navigation_buttons(ui, ctx, total_pages),
    )


async def choice_parameter_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext) -> RenderedMenu:
    total_pages = math.ceil(len(ctx.entry.entries) / ctx.max_elements_on_page)

    return RenderedMenu(
        ui=ui,
        context=ctx,
        text=await build_properties_text(ui, ctx),
        image=None,
        upper_keyboard=None,
        keyboard=await build_choice_parameter_keyboard(ui, ctx),
        footer_keyboard=await premade.build_navigation_buttons(ui, ctx, total_pages),
    )


async def formatters_list_menu_builder(
    ui: UIRegistry,
    ctx: PropertiesUIContext,
    fp_formatters: FormattersRegistry
) -> RenderedMenu:
    total_pages = math.ceil(len(fp_formatters) / ctx.max_elements_on_page)

    return RenderedMenu(
        ui=ui,
        context=ctx,
        text='Форматтеры',
        image=None,
        upper_keyboard=None,
        keyboard=await build_formatters_keyboard(ui, ctx, fp_formatters=fp_formatters),
        footer_keyboard=await premade.build_navigation_buttons(ui, ctx, total_pages),
    )