from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties.base import Entry
from funpayhub.lib.properties import ChoiceParameter, Properties, MutableParameter, ToggleParameter
from funpayhub.app.properties.flags import ParameterFlags as PropsFlags
from funpayhub.lib.telegram.ui.types import MenuRenderContext, ButtonRenderContext, Menu, Button
from funpayhub.app.telegram.ui.ids import MenuIds, ButtonIds
from aiogram.types import InlineKeyboardButton
from funpayhub.app.telegram.ui import premade


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui.registry import UIRegistry
    from funpayhub.lib.translater import Translater
    from funpayhub.app.properties import FunPayHubProperties



# ---------- PROPERTIES BUTTONS ----------
# Toggle parameter
async def toggle_param_button_builder(
    ui: UIRegistry,
    ctx: ButtonRenderContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Button:
    entry: ToggleParameter = ctx.data['entry']
    callback_data = ctx.menu_render_context.callback_data
    print(callback_data)
    translated_name = translater.translate(entry.name, properties.general.language.real_value)

    return Button(
        button_id=f'toggle_param',
        obj=InlineKeyboardButton(
            callback_data=cbs.NextParamValue(
                path=entry.path,
                history=callback_data.as_history() if callback_data is not None else []
            ).pack(),
            text=f'{"🟢" if entry.value else "🔴"} {translated_name}',
        )
    )


# Int / Float / String parameter
async def parameter_button_builder(
    ui: UIRegistry,
    ctx: ButtonRenderContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Button:
    entry: MutableParameter[Any] = ctx.data['entry']
    callback_data = ctx.menu_render_context.callback_data

    if not entry.has_flag(PropsFlags.PROTECT_VALUE):
        val_str = (
            f'{str(entry.value)[:20] + ('...' if len(str(entry.value)) > 20 else '')}'
        )
    else:
        val_str = '•' * 8

    return Button(
        button_id=f'param_change:{entry.path}',
        obj=InlineKeyboardButton(
            callback_data=cbs.ManualParamValueInput(
                path=entry.path,
                history=callback_data.as_history() if callback_data is not None else []
            ).pack(),
            text=f'{translater.translate(entry.name, properties.general.language.real_value)} '
                 f'【 {val_str} 】',
        )
    )


# List / Choice / Properties
async def build_open_entry_menu_button(
    ui: UIRegistry,
    ctx: ButtonRenderContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Button:
    """
    Дефолтный билдер для кнопки открытия меню параметра / категории параметров.

    Использует коллбэк `OpenEntryMenu`.
    """
    entry: Properties | MutableParameter[Any] = ctx.data['entry']
    callback_data = ctx.menu_render_context.callback_data
    print(f'FFF {callback_data}')

    return Button(
        button_id=f'param_change:{entry.path}',
        obj=InlineKeyboardButton(
            callback_data=cbs.OpenMenu(
                menu_id=MenuIds.properties_entry,
                history=callback_data.as_history() if callback_data is not None else [],
                data={'path': entry.path}
            ).pack(),
            text=translater.translate(entry.name, properties.general.language.real_value),
        )
    )



def _entry_text(entry: Entry, translater: Translater, language: str) -> str:
    return f"""<u><b>{translater.translate(entry.name, language)}</b></u>

<i>{translater.translate(entry.description, language)}</i>
"""


# Menus
async def properties_menu_builder(
    ui: UIRegistry,
    ctx: MenuRenderContext,
    translater: Translater,
    properties: FunPayHubProperties,
    data: dict[str, Any]
) -> Menu:
    keyboard = []
    entry: Properties = ctx.data['entry']

    for entry_id, sub_entry in entry.entries.items():
        if not isinstance(sub_entry, Properties | MutableParameter):  # skip immutable params
            continue

        try:
            button = await ui.build_button(
                button_id=ButtonIds.properties_entry,
                context=ctx,
                context_data={'path': sub_entry.path},
                data={**data},
            )
        except:
            import traceback
            print(traceback.format_exc())
            continue  # todo: err log

        keyboard.append([button])

    return Menu(
        text=_entry_text(entry, translater, properties.general.language.real_value),
        main_keyboard=keyboard,
        finalizer=premade.default_finalizer_factory(),
    )


async def choice_parameter_menu_builder(
    ui: UIRegistry,
    ctx: MenuRenderContext,
    translater: Translater,
    properties: FunPayHubProperties
) -> Menu:
    keyboard = []
    entry: ChoiceParameter[Any] = ctx.data['entry']
    callback_data = ctx.callback_data

    for choice in entry.choices.values():
        name = translater.translate(choice.name, properties.general.language.real_value)
        keyboard.append([
            Button(
                button_id=f'choice_param_value:{choice.id}:{entry.path}',
                obj=InlineKeyboardButton(
                    text=f'【 {name} 】' if entry.value == choice.id else name,
                    callback_data=cbs.ChooseParamValue(
                        path=entry.path,
                        choice_id=choice.id,
                        history=callback_data.as_history() if callback_data is not None else []
                    ).pack(),
                )
            )
        ])

    return Menu(
        text=_entry_text(entry, translater, properties.general.language.real_value),
        main_keyboard=keyboard,
        finalizer=premade.default_finalizer_factory(),
    )


async def list_parameter_menu_builder(
    ui: UIRegistry,
    ctx: MenuRenderContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Menu:
    keyboard = []
    entry = ctx.data['entry']
    mode = ctx.data.get('mode')
    callback_data = ctx.callback_data

    for index, val in enumerate(entry.value):
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
                obj=InlineKeyboardButton(
                    text=text,
                    callback_data=cbs.ListParamItemAction(
                        item_index=index,
                        path=entry.path,
                        action=mode,
                        history=callback_data.as_history() if callback_data is not None else []
                    ).pack()
                )
            )
        ])

    footer = [[]]
    if mode:
        footer[0].append(
            Button(
                button_id='cancel',
                obj=InlineKeyboardButton(
                    text='❌',
                    callback_data=cbs.OpenMenu(
                        menu_id=MenuIds.properties_entry,
                        menu_page=ctx.menu_page,
                        view_page=ctx.view_page,
                        history=callback_data.history if callback_data is not None else [],
                        data={'path': entry.path, 'mode': None}
                    ).pack()
                )
            )
        )

    footer[0].extend([
        Button(
            button_id='enable_move_up_mode',
            obj=InlineKeyboardButton(
                text='⬆️',
                callback_data=cbs.OpenMenu(
                    menu_id=MenuIds.properties_entry,
                    menu_page=ctx.menu_page,
                    view_page=ctx.view_page,
                    history=callback_data.history if callback_data is not None else [],
                    data={'path': entry.path, 'mode': 'move_up'}
                ).pack()
            )
        ),
        Button(
            button_id='enable_move_down_mode',
            obj=InlineKeyboardButton(
                text='⬇️',
                callback_data=cbs.OpenMenu(
                    menu_id=MenuIds.properties_entry,
                    menu_page=ctx.menu_page,
                    view_page=ctx.view_page,
                    history=callback_data.history if callback_data is not None else [],
                    data={'path': entry.path, 'mode': 'move_down'}
                ).pack()
            )
        ),
        Button(
            button_id='enable_remove_mode',
            obj=InlineKeyboardButton(
                text='🗑️',
                callback_data=cbs.OpenMenu(
                    menu_id=MenuIds.properties_entry,
                    menu_page=ctx.menu_page,
                    view_page=ctx.view_page,
                    history=callback_data.history if callback_data is not None else [],
                    data={'path': entry.path, 'mode': 'remove'}
                ).pack()
            )
        ),
        Button(
            button_id='add_list_item',
            obj=InlineKeyboardButton(
                text='➕',
                callback_data=cbs.ListParamAddItem(
                    path=entry.path,
                    history=callback_data.as_history() if callback_data is not None else []
                ).pack()
            )
        )
    ])

    return Menu(
        text=_entry_text(entry, translater, properties.general.language.real_value),
        main_keyboard=keyboard,
        footer_keyboard=footer,
        finalizer=premade.default_finalizer_factory(),
    )


async def parameter_menu_builder(
    ui: UIRegistry,
    ctx: MenuRenderContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Menu:
    entry: MutableParameter[Any] = ctx.data['entry']
    language = properties.general.language.real_value

    text = translater.translate('$enter_new_value_message', language=language).format(
        parameter_name=translater.translate(entry.name, language),
        parameter_description=translater.translate(entry.description, language),
        current_parameter_value=html.escape(str(entry.value)),
    )

    footer_keyboard = [[
        Button(
            button_id='clear_state',
            obj=InlineKeyboardButton(
                text=translater.translate('$clear_state', language),
                callback_data=cbs.Clear(
                    delete_message=False,
                    open_previous=True,
                    history=ctx.callback_data.history if ctx.callback_data is not None else [],
                ).pack()
            )
        )
    ]]

    return Menu(
        text=text,
        footer_keyboard=footer_keyboard,
        finalizer=premade.default_finalizer_factory(back_button=False),
    )


# Modifications
class PropertiesMenuModification:
    @staticmethod
    async def filter(ui: UIRegistry, ctx: MenuRenderContext, menu: Menu) -> bool:
        return ctx.menu_id == MenuIds.properties_entry and ctx.data.get('path') == []

    @staticmethod
    async def modification(
        ui: UIRegistry,
        ctx: MenuRenderContext,
        menu: Menu,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Menu:
        language = properties.general.language.real_value
        callback_data = ctx.callback_data

        menu.main_keyboard.append([
            Button(
                button_id='open_formatters_list',
                obj=InlineKeyboardButton(
                    text=translater.translate('$open_formatters_list', language),
                    callback_data=cbs.OpenMenu(
                        menu_id=MenuIds.formatters_list,
                        history=callback_data.as_history() if callback_data is not None else [],
                    ).pack()
                )
            )
        ])

        menu.main_keyboard.insert(1, [
            Button(
                button_id='open_current_chat_notifications',
                obj=InlineKeyboardButton(
                    text=translater.translate('$telegram_notifications', language),
                    callback_data=cbs.OpenMenu(
                        menu_id=MenuIds.tg_chat_notifications,
                        history=callback_data.as_history() if callback_data is not None else [],
                    ).pack()
                )
            )
        ])
        return menu
#
#
# async def add_formatters_list_button_modification(
#     ui: UIRegistry,
#     ctx: PropertiesUIContext,
#     menu: Menu
# ) -> Menu:
#     if not any([
#         ctx.entry.matches_path(['auto_response', '*', 'response_text']),
#         ctx.entry.matches_path(['review_reply', '*', 'review_reply_text']),
#         ctx.entry.matches_path(['review_reply', '*', 'chat_reply_text']),
#     ]):
#         return menu
#
#     menu.keyboard.append([
#         Button(
#             button_id='open_formatters_list',
#             text=ui.translater.translate('$open_formatters_list', ctx.language),
#             callback_data=cbs.OpenMenu(
#                 menu_id=MenuIds.FORMATTERS_LIST,
#                 history=ctx.callback.as_history()
#             ).pack()
#         )
#     ])
#     return menu
#
#
# async def add_add_button_for_commands_list(
#     ui: UIRegistry,
#     ctx: PropertiesUIContext,
#     menu: Menu
# ):
#     if not ctx.entry.matches_path(['auto_response']):
#         return menu
#
#     menu.footer_keyboard.append([
#         Button(
#             button_id='add_command',
#             text='$add_command',
#             callback_data=cbs.Dummy().pack()  # todo
#         )
#     ])
#
#     return menu