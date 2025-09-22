from __future__ import annotations
from aiogram.types import InlineKeyboardButton
from dataclasses import dataclass, replace
from collections.abc import Callable, Awaitable
from eventry.asyncio.callable_wrappers import CallableWrapper
from funpayhub.lib.properties import Properties, Parameter, MutableParameter
import funpayhub.lib.properties.parameter as param
from typing import Any
from funpayhub.lib.translater import Translater
import funpayhub.lib.telegram.callbacks as cbs
import math


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

    async def to_window(self, ui: UIRegistry, ctx: UIContext | PropertiesUIContext) -> Window:
        ...

    def copy_and_transform(self) -> Menu:
        if isinstance(self.text, str | None | CallableWrapper):
            text = self.text
        else:
            text = CallableWrapper(self.text)

        if isinstance(self.image, str | None | CallableWrapper):
            image = self.image
        else:
            image = CallableWrapper(self.image)

        u_k, k, f_k = [
            CallableWrapper(i) if not isinstance(i, list | CallableWrapper | None) else i
            for i in [self.upper_keyboard, self.keyboard, self.footer_keyboard]
        ]

        return Menu(
            text=text,
            image=image,
            upper_keyboard=u_k,
            keyboard=k,
            footer_keyboard=f_k,
        )


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
    current_callback: str
    callbacks_history: list[str]


@dataclass
class PropertiesUIContext(UIContext):
    entry: Properties | MutableParameter


@dataclass
class InplaceChangeableParameter:
    button_builder: Callable[..., Button | Awaitable[Button]]


@dataclass
class ManualChangeableParameter:
    button_builder: Callable[..., Button | Awaitable[Button]]
    next_menu: Callable[..., Menu | Awaitable[Menu]]


@dataclass
class MenuChangeableParameter:
    button_builder: Callable[..., Button | Awaitable[Button]]
    next_menu: Callable[..., Menu | Awaitable[Menu]]


@dataclass
class PropertiesMenu:
    button_builder: Callable[..., Button | Awaitable[Button]]
    next_menu: Callable[..., Menu | Awaitable[Menu]]


# Defaults
# ToggleParameter
async def build_toggle_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
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
async def build_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
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


async def build_parameter_change_menu(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
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
async def build_long_value_parameter_button(ui: UIRegistry, ctx: PropertiesUIContext) -> Button:
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
async def build_choice_parameter_menu(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    if not isinstance(ctx.entry, Parameter):
        raise ValueError(f'')


# properties
async def build_properties_keyboard(ui: UIRegistry, ctx: PropertiesUIContext) -> Keyboard:
    keyboard = []

    first_element = ctx.page * ctx.max_elements_on_page
    last_element = first_element + ctx.max_elements_on_page
    entries = list(ctx.entry.entries.items())[first_element:last_element]

    for entry_id, entry in entries:
        if type(entry) not in ui.default_properties_renderers:
            continue

        builder = ui.default_properties_renderers[type(entry)]

        btn_ctx = replace(
            ctx,
            page=0,
            callbacks_history=ctx.callbacks_history + [ctx.current_callback]
        )
        keyboard.append([await builder.button_builder(btn_ctx)])
    return keyboard


async def build_properties_footer(ui: UIContext, ctx: PropertiesUIContext) -> Keyboard:
    total_pages = math.ceil(len(ctx.entry) / ctx.max_elements_on_page)
    new_history = ctx.callbacks_history + [ctx.current_callback]

    page_amount_cb = cbs.ManualPageChange(total_pages=total_pages).pack() \
        if total_pages > 1 \
        else cbs.Dummy().pack()

    page_amount_cb = '->'.join([*new_history, page_amount_cb])

    page_amount_btn = InlineKeyboardButton(
        text=f'{ctx.page + (1 if total_pages else 0)} / {total_pages}',
        callback_data=page_amount_cb
    )

    to_first_cb = cbs.ChangePageTo(page=0).pack() if ctx.page > 0 else cbs.Dummy().pack()
    to_first_cb = '->'.join([*new_history, to_first_cb])

    to_first_btn = InlineKeyboardButton(
        text='⏪' if ctx.page > 0 else '❌',
        callback_data=to_first_cb
    )

    to_last_cb = cbs.ChangePageTo(page=total_pages-1).pack() if ctx.page < total_pages-1 else cbs.Dummy().pack()
    to_last_cb = '->'.join([*new_history, to_last_cb])

    to_last_btn = InlineKeyboardButton(
        text='⏩' if ctx.page < total_pages-1 else '❌',
        callback_data=to_last_cb
    )

    to_previous_cb = cbs.ChangePageTo(page=ctx.page-1).pack() if ctx.page > 0 else cbs.Dummy().pack()
    to_previous_cb = '->'.join([*new_history, to_previous_cb])
    to_previous_btn = InlineKeyboardButton(
        text='◀️' if ctx.page > 0 else '❌',
        callback_data=to_previous_cb
    )

    to_next_cb = cbs.ChangePageTo(page=ctx.page+1).pack() if ctx.page < total_pages - 1 else cbs.Dummy().pack()
    to_next_cb = '->'.join([*new_history, to_next_cb])

    to_next_btn = InlineKeyboardButton(
        text='▶️' if ctx.page < total_pages - 1 else '❌',
        callback_data=to_next_cb
    )

    return [
        Button(id='to_first_page', obj=to_first_btn),
        Button(id='to_previous_page', obj=to_previous_btn),
        Button(id='page_counter', obj=page_amount_btn),
        Button(id='to_next_page', obj=to_next_btn),
        Button(id='to_last_page', obj=to_last_btn),
    ]


async def build_properties_text(ui: UIRegistry, ctx: PropertiesUIContext) -> str:
    return f"""</u><b>{ctx.translater.translate(ctx.entry.name, ctx.language)}</b></u>

<i>{ctx.translater.translate(ctx.entry.description, ctx.language)}</i>
"""

async def properties_menu_builder(ui: UIRegistry, ctx: PropertiesUIContext) -> Menu:
    return Menu(
        text=build_properties_text,
        image=None,
        upper_keyboard=None,
        keyboard=build_properties_keyboard,
        footer_keyboard=build_properties_footer
    )


# Defaults
TOGGLE_UI = InplaceChangeableParameter(
    button_builder=build_toggle_parameter_button
)

MANUAL_CHANGE_PARAM_UI = ManualChangeableParameter(
    button_builder=build_parameter_button,
    next_menu=build_parameter_change_menu,
)

PROPERTIES_UI = PropertiesMenu(
    button_builder=build_long_value_parameter_button,
    next_menu=properties_menu_builder,
)

class UIRegistry:
    def __init__(self):
        self.default_properties_renderers: dict[type[MutableParameter | Properties], Any] = {
            param.ToggleParameter: TOGGLE_UI,
            param.IntParameter: MANUAL_CHANGE_PARAM_UI,
            param.FloatParameter: MANUAL_CHANGE_PARAM_UI,
            param.StringParameter: MANUAL_CHANGE_PARAM_UI,
            param.ChoiceParameter: ...,
            param.ListParameter: ...,
            Properties: PROPERTIES_UI
        }
        self.properties_renderers_overloads: dict[type[MutableParameter | Properties], Any] = {}

        self.menus: dict[str, Menu] = {}
        self.menus_overloads: dict[str, Menu] = {}

    async def build_properties_ui(self, ctx: PropertiesUIContext) -> Window:
        """
        :param ctx:
        :return:
        """
        if type(ctx.entry) not in self.default_properties_renderers:
            raise ValueError(f'Unknown entry type: {type(ctx.entry)}')

        ui = self.default_properties_renderers[type(ctx.entry)]
        menu: Menu = await ui.next_menu()


    async def build_menu(self, menu: str, ctx: PropertiesUIContext) -> Window: ...