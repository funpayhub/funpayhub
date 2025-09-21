from __future__ import annotations
from aiogram.types import InlineKeyboardButton
from dataclasses import dataclass
from collections.abc import Callable, Awaitable
from eventry.asyncio.callable_wrappers import CallableWrapper
from funpayhub.lib.properties import Properties, Parameter, MutableParameter
import funpayhub.lib.properties.parameter as param
from typing import Any
from funpayhub.lib.translater import Translater
import funpayhub.lib.telegram.callbacks as cbs


type Keyboard = list[Button | list[Button]]
type KeyboardOrButton = Button | Keyboard
type CallableValue[R] = Callable[..., R | Awaitable[R]] | CallableWrapper[R] | R


@dataclass
class Button:
    """
    Готовый объект кнопки с уже переведенным именем, но не хэшированным callback.
    """
    id: str
    obj: InlineKeyboardButton


@dataclass
class Menu:
    """
    Объект меню.
    """
    text: CallableValue[str] | None = None
    image: CallableValue[str] | None = None
    upper_keyboard: CallableValue[Keyboard] | None = None
    keyboard: CallableValue[Keyboard] | None = None
    footer_keyboard: CallableValue[Keyboard] | None = None


@dataclass
class Window:
    """
    Итоговый объект меню после всех модификаций.
    """
    text: str | None = None
    image: str | None = None
    keyboard: Keyboard | None = None


@dataclass
class UIContext:
    translater: Translater
    language: str
    max_elements_on_page: int
    page: int


@dataclass
class PropertiesUIContext(UIContext):
    entry: Properties | MutableParameter
    callbacks_history: list[str]


@dataclass
class InplaceChangeableParameter:
    button_builder: Callable[..., Button | Awaitable[Button]]


@dataclass
class ManualChangeableParameter:
    button_builder: Callable[..., Button | Awaitable[Button]]
    change_message_builder: Callable[..., Menu | Awaitable[Menu]]


@dataclass
class MenuChangeableParameter:
    button_builder: Callable[..., Menu | Awaitable[Menu]]
    change_menu_builder: Callable[..., Menu | Awaitable[Menu]]


# Defaults
# ToggleParameter
async def build_toggle_parameter_button(ctx: PropertiesUIContext) -> Button:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError(f'')  # todo

    btn_callback = cbs.NextParamValue(path=ctx.entry.path).pack()
    total_callback = '->'.join([*ctx.callbacks_history, btn_callback])
    translated_name = ctx.translater.translate(ctx.entry.name, ctx.language)

    btn = InlineKeyboardButton(
        callback_data=total_callback,
        text=f'{"🟢" if ctx.entry.value else "🔴"} {translated_name}',
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


# Int / Float / String parameter
async def build_parameter_button(ctx: PropertiesUIContext) -> Button:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError(f'')

    btn_callback = cbs.ManualParamValueInput(path=ctx.entry.path).pack()
    total_callback = '->'.join([*ctx.callbacks_history, btn_callback])
    translated_name = ctx.translater.translate(ctx.entry.name, ctx.language)
    val_str = f'{str(ctx.entry.value)[:20] + ("..." if len(str(ctx.entry.value)) > 20 else "")}'

    btn = InlineKeyboardButton(
        callback_data=total_callback,
        text=f'{translated_name} 【 {val_str} 】'
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


async def build_parameter_change_menu(ctx: PropertiesUIContext) -> Menu:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError(f'')

    text = ctx.translater.translate('$enter_new_value_message', language=ctx.language).format(
        parameter_name=ctx.translater.translate(ctx.entry.name, ctx.language),
        parameter_description=ctx.translater.translate(ctx.entry.description, ctx.language),
        current_parameter_value=str(ctx.entry.value)
    )

    btn_callback = cbs.Clear().pack()
    total_callback = '->'.join([*ctx.callbacks_history, btn_callback])

    footer_keyboard = [
        Button(
            id='clear_state',
            obj=InlineKeyboardButton(
                text=ctx.translater.translate('$clear_state', ctx.language),
                callback_data=total_callback
            )
        )
    ]

    return Menu(text=text, footer_keyboard=footer_keyboard)


# List / Choice
async def build_long_value_parameter_button(ctx: PropertiesUIContext) -> Button:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError(f'')

    btn_callback = cbs.MenuParamValueInput(path=ctx.entry.path).pack()
    total_callback = '->'.join([*ctx.callbacks_history, btn_callback])
    translated_name = ctx.translater.translate(ctx.entry.name, ctx.language)

    btn = InlineKeyboardButton(
        callback_data=total_callback,
        text=translated_name
    )

    return Button(id=f'param_change:{ctx.entry.path}', obj=btn)


# choice builder
async def build_choice_parameter_menu(ctx: PropertiesUIContext) -> Menu:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError(f'')






class UIRegistry:
    def __init__(self):
        self.default_properties_renderers: dict[type[MutableParameter | Properties], Any] = {
            param.ToggleParameter: ...,
            param.IntParameter: ...,
            param.FloatParameter: ...,
            param.StringParameter: ...,
            param.ChoiceParameter: ...,
            param.ListParameter: ...,
            Properties: ...
        }
        self.properties_renderers_overloads: dict[type[MutableParameter | Properties], Any] = {}

        self.menus: dict[str, Menu] = {}
        self.menus_overloads: dict[str, Menu] = {}

    async def build_properties_ui(self, ctx: PropertiesUIContext) -> Window:
        """
        :param ctx:
        :return:
        """

    async def build_menu(self, menu: str, ctx: PropertiesUIContext) -> Window: ...