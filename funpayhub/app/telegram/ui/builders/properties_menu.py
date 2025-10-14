from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any
from dataclasses import replace

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.loggers import telegram_ui as logger
from funpayhub.lib.properties import ChoiceParameter, Properties, MutableParameter, ListParameter
from funpayhub.app.properties.flags import ParameterFlags as PropsFlags
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.telegram.ui.types import Menu, Button, Keyboard, UIContext
from funpayhub.lib.translater import Translater

from .. import premade, ids as ids
from ..ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


# Main properties menu builder
async def build_properties_entry_menu(ui: UIRegistry, ctx: UIContext, data) -> Menu:
    properties = data.get('properties', None)
    if not properties or not isinstance(properties, FunPayHubProperties):
        raise RuntimeError('Not valid properties.')  # todo: error text

    path = data.get('entry_path', None)
    if path is None or not isinstance(path, list):
        raise RuntimeError('Not valid path.')  # todo: error text

    entry = properties.get_entry(path)
    if not isinstance(entry, Properties | MutableParameter):
        raise ValueError(f'No entry at path {path}.')  # todo: error text

    menu = ui.properties_ui_registry.menu_builder(type(entry))
    if not menu:
        raise ValueError(f'No menu builder for entry with type {type(entry)!r}.')

    return await menu((ui, ctx), data | {'entry_obj': entry})


# ---------- PROPERTIES BUTTONS ----------
# Toggle parameter
async def build_toggle_parameter_button(ui: UIRegistry, ctx: UIContext, translater: Translater, entry_obj: MutableParameter[Any]) -> Button:
    """
    Дефолтный билдер кнопки параметра-переключателя.

    Использует коллбэк `NextParamValue`.
    """
    logger.debug(f'Building toggle parameter button for {entry_obj.path}')
    translated_name = translater.translate(entry_obj.name, ctx.language)

    return Button(
        button_id=f'{ids.TOGGLE_PARAM_BTN}:{entry_obj.path}',
        obj=InlineKeyboardButton(
            callback_data=cbs.NextParamValue(
                path=entry_obj.path,
                history=ctx.callback.as_history()
            ).pack(),
            text=f'{"🟢" if entry_obj.value else "🔴"} {translated_name}',
        )
    )


# Int / Float / String parameter
async def build_parameter_button(ui: UIRegistry, ctx: UIContext, translater: Translater, entry_obj: MutableParameter[Any]) -> Button:
    """
    Дефолтный билдер для кнопки параметра с ручным вводом значения (через сообщение).

    Отображает значение параметра (первые 20 символов) в 【 скобках 】.

    Если у параметра есть флаг `PROTECT_VALUE`, отображает значение в виде `••••••••`.

    Использует коллбэк `ManualParamValueInput`.
    """

    logger.debug(f'Building default parameter button for {entry_obj.path}')

    if not entry_obj.has_flag(PropsFlags.PROTECT_VALUE):
        val_str = (
            f'{str(entry_obj.value)[:20] + ("..." if len(str(entry_obj.value)) > 20 else "")}'
        )
    else:
        val_str = '•' * 8

    return Button(
        button_id=f'param_change:{entry_obj.path}',
        obj=InlineKeyboardButton(
            callback_data=cbs.ManualParamValueInput(
                path=entry_obj.path,
                history=ctx.callback.as_history()
            ).pack(),
            text=f'{translater.translate(entry_obj.name, ctx.language)} 【 {val_str} 】',
        )
    )


# List / Choice / Properties
async def build_open_entry_menu_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
    """
    Дефолтный билдер для кнопки открытия меню параметра / категории параметров.

    Использует коллбэк `OpenEntryMenu`.
    """
    return Button(
        button_id=f'param_change:{ctx.entry.path}',
        callback_data=cbs.OpenEntryMenu(
            path=ctx.entry.path,
            history=ctx.callback.as_history()
        ).pack(),
        text=ui.translater.translate(ctx.entry.name, ctx.language),
    )


# ---------- PROPERTIES KEYBOARDS ----------
# Properties keyboard
async def build_properties_keyboard(ui: UIRegistry, ctx: PropertiesUIContext, **data) -> Keyboard:
    assert isinstance(ctx.entry, Properties)
    keyboard = []

    for entry_id, entry in ctx.entry.entries.items():
        if not isinstance(entry, Properties | MutableParameter):  # skip immutable params
            continue

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
    assert isinstance(ctx.entry, ChoiceParameter)
    keyboard = []

    for choice in ctx.entry.choices.values():
        name = ui.translater.translate(choice.name, ctx.language)
        keyboard.append([
            Button(
                button_id=f'choice_param_value:{choice.id}:{ctx.entry.path}',
                text=f'【 {name} 】' if ctx.entry.value == choice.id else name,
                callback_data=cbs.ChooseParamValue(
                    path=ctx.entry.path,
                    choice_id=choice.id,
                    history=ctx.callback.as_history()
                ).pack(),
            )
        ])

    return keyboard


async def build_list_parameter_keyboard(ui: UIRegistry, ctx: PropertiesUIContext) -> Keyboard:
    assert isinstance(ctx.entry, ListParameter)
    keyboard = []
    mode = ctx.callback.data.get('mode')

    for index, val in enumerate(ctx.entry.value):
        if mode == 'move_up':
            text = f'⬆️ {val}'
        elif mode == 'move_down':
            text = f'⬇️ {val}'
        elif mode == 'remove':
            text = f'🗑️ {val}'
        else:
            text = str(val)

        keyboard.append([
            Button(
                button_id='temp',
                text=text,
                callback_data=cbs.ListParamItemAction(
                    item_index=index,
                    path=ctx.entry.path,
                    action=mode,
                    history=ctx.callback.as_history()
                ).pack()
            )
        ])
    return keyboard


async def build_list_parameter_footer(ui: UIRegistry, ctx: PropertiesUIContext) -> Keyboard:
    keyboard = [[]]
    mode = ctx.callback.data.get('mode')
    if mode:
        keyboard[0].append(
            Button(
                button_id='cancel',
                text='❌',
                callback_data=cbs.ChangeListParamViewMode(
                    mode=None,
                    history=ctx.callback.as_history()
                ).pack()
            )
        )

    keyboard[0].extend([
        Button(
            button_id='enable_move_up_mode',
            text='⬆️',
            callback_data=cbs.ChangeListParamViewMode(
                mode='move_up',
                history=ctx.callback.as_history()
            ).pack()
        ),
        Button(
            button_id='enable_move_down_mode',
            text='⬇️',
            callback_data=cbs.ChangeListParamViewMode(
                mode='move_down',
                history=ctx.callback.as_history()
            ).pack()
        ),
        Button(
            button_id='enable_remove_mode',
            text='🗑️',
            callback_data=cbs.ChangeListParamViewMode(
                mode='remove',
                history=ctx.callback.as_history()
            ).pack()
        ),
        Button(
            button_id='add_list_item',
            text='➕',
            callback_data=cbs.ListParamAddItem(
                path=ctx.entry.path,
                history=ctx.callback.as_history()
            ).pack()
        )
    ])
    return keyboard



async def build_properties_text(ui: UIRegistry, ctx: PropertiesUIContext) -> str:
    return f"""<u><b>{ui.translater.translate(ctx.entry.name, ctx.language)}</b></u>

<i>{ui.translater.translate(ctx.entry.description, ctx.language)}</i>
"""


# Menus
async def properties_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext, **data) -> Menu:
    return Menu(
        ui=ui,
        context=ctx,
        text=await build_properties_text(ui, ctx),
        image=None,
        header_keyboard=None,
        keyboard=await build_properties_keyboard(ui, ctx, **data),
        finalizer=premade.default_finalizer_factory(),
    )


async def choice_parameter_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    return Menu(
        ui=ui,
        context=ctx,
        text=await build_properties_text(ui, ctx),
        image=None,
        keyboard=await build_choice_parameter_keyboard(ui, ctx),
        finalizer=premade.default_finalizer_factory(),
    )


async def list_parameter_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    return Menu(
        ui=ui,
        context=ctx,
        text=await build_properties_text(ui, ctx),
        image=None,
        keyboard=await build_list_parameter_keyboard(ui, ctx),
        footer_keyboard=await build_list_parameter_footer(ui, ctx),
        finalizer=premade.default_finalizer_factory(),
    )


async def parameter_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    assert isinstance(ctx.entry, MutableParameter)

    text = ui.translater.translate('$enter_new_value_message', language=ctx.language).format(
        parameter_name=ui.translater.translate(ctx.entry.name, ctx.language),
        parameter_description=ui.translater.translate(ctx.entry.description, ctx.language),
        current_parameter_value=html.escape(str(ctx.entry.value)),
    )

    footer_keyboard = [
        Button(
            button_id='clear_state',
            text=ui.translater.translate('$clear_state', ctx.language),
            callback_data=cbs.Clear(
                delete_message=False,
                open_previous=True,
                history=ctx.callback.history
            ).pack()
        )
    ]

    return Menu(
        ui=ui,
        context=ctx,
        text=text,
        footer_keyboard=[footer_keyboard],
        finalizer=premade.default_finalizer_factory(back_button=False),
    )


# Modifications
async def funpayhub_properties_menu_modification(
    ui: UIRegistry,
    ctx: PropertiesUIContext,
    menu: Menu
) -> Menu:
    if not ctx.entry.matches_path([]):
        return menu

    menu.keyboard.append([
        Button(
            button_id='open_formatters_list',
            text=ui.translater.translate('$open_formatters_list', ctx.language),
            callback_data=cbs.OpenMenu(
                menu_id=MenuIds.FORMATTERS_LIST,
                history=ctx.callback.as_history(),
            ).pack()
        )
    ])

    menu.keyboard.insert(1, [
        Button(
            button_id='open_current_chat_notifications',
            text=ui.translater.translate('$telegram_notifications', ctx.language),
            callback_data=cbs.OpenMenu(
                menu_id=MenuIds.TG_CHAT_NOTIFICATIONS,
                history=ctx.callback.as_history(),
            ).pack()
        )
    ])
    return menu


async def add_formatters_list_button_modification(
    ui: UIRegistry,
    ctx: PropertiesUIContext,
    menu: Menu
) -> Menu:
    if not any([
        ctx.entry.matches_path(['auto_response', '*', 'response_text']),
        ctx.entry.matches_path(['review_reply', '*', 'review_reply_text']),
        ctx.entry.matches_path(['review_reply', '*', 'chat_reply_text']),
    ]):
        return menu

    menu.keyboard.append([
        Button(
            button_id='open_formatters_list',
            text=ui.translater.translate('$open_formatters_list', ctx.language),
            callback_data=cbs.OpenMenu(
                menu_id=MenuIds.FORMATTERS_LIST,
                history=ctx.callback.as_history()
            ).pack()
        )
    ])
    return menu


async def add_add_button_for_commands_list(
    ui: UIRegistry,
    ctx: PropertiesUIContext,
    menu: Menu
):
    if not ctx.entry.matches_path(['auto_response']):
        return menu

    menu.footer_keyboard.append([
        Button(
            button_id='add_command',
            text='$add_command',
            callback_data=cbs.Dummy().pack()  # todo
        )
    ])

    return menu