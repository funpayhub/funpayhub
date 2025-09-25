from __future__ import annotations

import html
import math
from typing import TYPE_CHECKING
from dataclasses import replace

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.loggers import tg_ui_logger as logger
from funpayhub.lib.properties import Parameter, ChoiceParameter, ToggleParameter
from funpayhub.lib.properties.flags import DefaultPropertiesFlags as Flags
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, UIContext, PropertiesUIContext
from funpayhub.lib.hub.text_formatters import FormattersRegistry

from . import premade, button_ids as ids


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


# Finalizer
async def default_finalizer(ui: UIRegistry, ctx: PropertiesUIContext, menu: Menu) -> Menu:
    if not menu.footer_keyboard:
        menu.footer_keyboard = []

    total_pages = math.ceil(len(menu.keyboard) / ctx.max_elements_on_page) if menu.keyboard else 0
    navigation_buttons = await premade.build_menu_navigation_buttons(ui, ctx, total_pages)
    menu.footer_keyboard.extend(navigation_buttons)

    if menu.keyboard:
        first_index = ctx.menu_page * ctx.max_elements_on_page
        last_index = first_index + ctx.max_elements_on_page
        menu.keyboard = menu.keyboard[first_index:last_index]

    return menu


# ToggleParameter
async def build_toggle_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    """
    Дефолтный билдер кнопки параметра-переключателя.

    Использует коллбэк `NextParamValue`.
    """
    logger.debug(f'Building toggle parameter button for {ctx.entry.path}')

    if not isinstance(ctx.entry, ToggleParameter):
        raise ValueError(f'{type(ctx.entry)} is not a ToggleParameter.')

    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    btn = InlineKeyboardButton(
        callback_data=cbs.NextParamValue(
            path=ctx.entry.path,
            history=[ctx.callback.pack()]
        ).pack(),
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

    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    if Flags.PROTECT_VALUE not in ctx.entry._flags:
        val_str = (
            f'{str(ctx.entry.value)[:20] + ("..." if len(str(ctx.entry.value)) > 20 else "")}'
        )
    else:
        val_str = '•' * 8

    btn = InlineKeyboardButton(
        callback_data=cbs.ManualParamValueInput(
            path=ctx.entry.path,
            history=[ctx.callback.pack()]
        ).pack(),
        text=f'{translated_name} 【 {val_str} 】',
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


# List / Choice / Properties button
async def build_open_menu_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    """
    Дефолтный билдер для кнопки открытия меню параметра / категории параметров.

    Использует коллбэк `OpenEntryMenu`.
    """
    translated_name = ui.translater.translate(ctx.entry.name, ctx.language)

    btn = InlineKeyboardButton(
        callback_data=cbs.OpenEntryMenu(
            path=ctx.entry.path,
            history=[ctx.callback.pack()]
        ).pack(),
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
            menu_page=0,
            view_page=0,
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
        name = ui.translater.translate(choice.name, ctx.language)

        btn = InlineKeyboardButton(
            text=f'【 {name} 】' if ctx.entry.value == index else name,
            callback_data=cbs.ChooseParamValue(
                path=ctx.entry.path,
                choice_index=index,
                history=[ctx.callback.pack()]
            ).pack(),
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


async def build_parameter_change_menu(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
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
                callback_data=cbs.Clear(history=ctx.callback.history).pack()
            ),
        ),
    ]

    return Menu(
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
async def build_formatters_keyboard(
    ui: UIRegistry, ctx: UIContext, fp_formatters: FormattersRegistry
) -> Keyboard:
    keyboard = []
    for formatter in fp_formatters:
        btn = InlineKeyboardButton(
            text=ui.translater.translate(formatter.name, ctx.language),
            callback_data=cbs.OpenMenu(
                menu_id='fph-formatter-info',
                data={'formatter_id':formatter.key},
                history=[ctx.callback.pack()]
            ).pack(),
        )
        keyboard.append([Button(id=f'open_formatter_info:{formatter.key}', obj=btn)])
    return keyboard


async def properties_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext, **data) -> Menu:
    return Menu(
        ui=ui,
        context=ctx,
        text=await build_properties_text(ui, ctx),
        image=None,
        header_keyboard=None,
        keyboard=await build_properties_keyboard(ui, ctx, **data),
        finalizer=default_finalizer,
    )


async def choice_parameter_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    return Menu(
        ui=ui,
        context=ctx,
        text=await build_properties_text(ui, ctx),
        image=None,
        header_keyboard=None,
        keyboard=await build_choice_parameter_keyboard(ui, ctx),
        finalizer=default_finalizer,
    )


async def formatters_list_menu_builder(
    ui: UIRegistry,
    ctx: PropertiesUIContext,
    fp_formatters: FormattersRegistry,
) -> Menu:
    return Menu(
        ui=ui,
        context=ctx,
        text='Форматтеры',
        image=None,
        header_keyboard=None,
        keyboard=await build_formatters_keyboard(ui, ctx, fp_formatters=fp_formatters),
        finalizer=default_finalizer,
    )
