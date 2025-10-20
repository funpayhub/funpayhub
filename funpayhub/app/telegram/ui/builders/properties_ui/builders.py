from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any

from aiogram.types import InlineKeyboardButton

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.app.telegram.ui import premade
from funpayhub.app.telegram.ui.ids import MenuIds, ButtonIds
from funpayhub.lib.properties.base import Entry
from funpayhub.app.properties.flags import ParameterFlags as PropsFlags
from funpayhub.lib.telegram.ui.types import Menu, Button
from funpayhub.app.telegram.ui.builders.properties_ui.context import (
    PropertiesMenuContext,
    PropertiesButtonContext,
)


if TYPE_CHECKING:
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.lib.translater import Translater
    from funpayhub.lib.telegram.ui.registry import UIRegistry


async def toggle_param_button_builder(
    ctx: PropertiesButtonContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Button:
    callback_data = ctx.menu_render_context.callback_data
    translated_name = translater.translate(ctx.entry.name, properties.general.language.real_value)

    return Button(
        button_id='toggle_param',
        obj=InlineKeyboardButton(
            callback_data=cbs.NextParamValue(
                path=ctx.entry.path,
                history=callback_data.as_history() if callback_data is not None else [],
            ).pack(),
            text=f'{"🟢" if ctx.entry.value else "🔴"} {translated_name}',
        ),
    )


# Int / Float / String parameter
async def parameter_button_builder(
    ctx: PropertiesButtonContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Button:
    callback_data = ctx.menu_render_context.callback_data

    if not ctx.entry.has_flag(PropsFlags.PROTECT_VALUE):
        val_str = (
            f'{str(ctx.entry.value)[:20] + ("..." if len(str(ctx.entry.value)) > 20 else "")}'
        )
    else:
        val_str = '•' * 8

    return Button(
        button_id=f'param_change:{ctx.entry.path}',
        obj=InlineKeyboardButton(
            callback_data=cbs.ManualParamValueInput(
                path=ctx.entry.path,
                history=callback_data.as_history() if callback_data is not None else [],
            ).pack(),
            text=f'{translater.translate(ctx.entry.name, properties.general.language.real_value)} '
            f'【 {val_str} 】',
        ),
    )


# List / Choice / Properties
async def open_entry_menu_button_builder(
    ctx: PropertiesButtonContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Button:
    callback_data = ctx.menu_render_context.callback_data

    return Button(
        button_id=f'param_change:{ctx.entry.path}',
        obj=InlineKeyboardButton(
            callback_data=cbs.OpenEntryMenu(
                path=ctx.entry.path,
                history=callback_data.as_history() if callback_data is not None else [],
            ).pack(),
            text=translater.translate(ctx.entry.name, properties.general.language.real_value),
        ),
    )


def _entry_text(entry: Entry, translater: Translater, language: str) -> str:
    return f"""<u><b>{translater.translate(entry.name, language)}</b></u>

<i>{translater.translate(entry.description, language)}</i>
"""


# Menus
async def properties_menu_builder(
    ctx: PropertiesMenuContext,
    translater: Translater,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    data: dict[str, Any],
) -> Menu:
    keyboard = []

    for entry_id, sub_entry in ctx.entry.entries.items():
        if not isinstance(sub_entry, Properties | MutableParameter):  # skip immutable params
            continue

        try:
            button_ctx = PropertiesButtonContext(
                button_id=ButtonIds.properties_entry,
                menu_render_context=ctx,
                entry=sub_entry,
            )
            button = await tg_ui.build_button(
                button_id=ButtonIds.properties_entry,
                context=button_ctx,
                data={**data},
            )
        except:
            import traceback

            print(traceback.format_exc())
            continue  # todo: err log

        keyboard.append([button])

    return Menu(
        text=_entry_text(ctx.entry, translater, properties.general.language.real_value),
        main_keyboard=keyboard,
        finalizer=premade.default_finalizer_factory(),
    )


async def choice_parameter_menu_builder(
    ctx: PropertiesMenuContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Menu:
    keyboard = []
    callback_data = ctx.callback_data

    for choice in ctx.entry.choices.values():
        name = translater.translate(choice.name, properties.general.language.real_value)
        keyboard.append(
            [
                Button(
                    button_id=f'choice_param_value:{choice.id}:{ctx.entry.path}',
                    obj=InlineKeyboardButton(
                        text=f'【 {name} 】' if ctx.entry.value == choice.id else name,
                        callback_data=cbs.ChooseParamValue(
                            path=ctx.entry.path,
                            choice_id=choice.id,
                            history=callback_data.as_history()
                            if callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ]
        )

    return Menu(
        text=_entry_text(ctx.entry, translater, properties.general.language.real_value),
        main_keyboard=keyboard,
        finalizer=premade.default_finalizer_factory(),
    )


async def list_parameter_menu_builder(
    ctx: PropertiesMenuContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Menu:
    keyboard = []
    mode = ctx.data.get('mode')
    callback_data = ctx.callback_data

    for index, val in enumerate(ctx.entry.value):
        if mode == 'move_up':
            text = f'⬆️ {val}'
        elif mode == 'move_down':
            text = f'⬇️ {val}'
        elif mode == 'remove':
            text = f'🗑️ {val}'
        else:
            text = str(val)

        keyboard.append(
            [
                Button(
                    button_id='temp',
                    obj=InlineKeyboardButton(
                        text=text,
                        callback_data=cbs.ListParamItemAction(
                            item_index=index,
                            path=ctx.entry.path,
                            action=mode,
                            history=callback_data.as_history()
                            if callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ]
        )

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
                        data={'path': ctx.entry.path, 'mode': None},
                    ).pack(),
                ),
            ),
        )

    mode_data = {
        'enable_move_up_mode': ('⬆️', 'move_up'),
        'enable_move_down_mode': ('⬇️', 'move_down'),
        'enable_remove_mode': ('🗑️', 'remove'),
    }
    buttons = []
    for button_id, (text, mode) in mode_data.items():
        buttons.append(
            Button(
                button_id=button_id,
                obj=InlineKeyboardButton(
                    text=text,
                    callback_data=cbs.OpenMenu(
                        menu_id=MenuIds.properties_entry,
                        menu_page=ctx.menu_page,
                        view_page=ctx.view_page,
                        history=callback_data.history if callback_data is not None else [],
                        data={'path': ctx.entry.path, 'mode': mode},
                    ).pack(),
                ),
            ),
        )
    footer[0].extend(buttons)

    footer[0].append(
        Button(
            button_id='add_list_item',
            obj=InlineKeyboardButton(
                text='➕',
                callback_data=cbs.ListParamAddItem(
                    path=ctx.entry.path,
                    history=callback_data.as_history() if callback_data is not None else [],
                ).pack(),
            ),
        ),
    )

    return Menu(
        text=_entry_text(ctx.entry, translater, properties.general.language.real_value),
        main_keyboard=keyboard,
        footer_keyboard=footer,
        finalizer=premade.default_finalizer_factory(),
    )


async def param_value_manual_input_menu_builder(
    ctx: PropertiesMenuContext,
    translater: Translater,
    properties: FunPayHubProperties,
) -> Menu:
    language = properties.general.language.real_value

    text = translater.translate('$enter_new_value_message', language=language).format(
        parameter_name=translater.translate(ctx.entry.name, language),
        parameter_description=translater.translate(ctx.entry.description, language),
        current_parameter_value=html.escape(str(ctx.entry.value)),
    )

    footer_keyboard = [
        [
            Button(
                button_id='clear_state',
                obj=InlineKeyboardButton(
                    text=translater.translate('$clear_state', language),
                    callback_data=cbs.Clear(
                        delete_message=False,
                        open_previous=True,
                        history=ctx.callback_data.history if ctx.callback_data is not None else [],
                    ).pack(),
                ),
            ),
        ]
    ]

    return Menu(
        text=text,
        footer_keyboard=footer_keyboard,
        finalizer=premade.default_finalizer_factory(back_button=False),
    )


# Modifications
class PropertiesMenuModification:
    @staticmethod
    async def filter(ctx: PropertiesMenuContext, menu: Menu) -> bool:
        return ctx.menu_id == MenuIds.properties_entry and ctx.entry.matches_path([])

    @staticmethod
    async def modification(
        ctx: PropertiesMenuContext,
        menu: Menu,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Menu:
        language = properties.general.language.real_value
        callback_data = ctx.callback_data

        menu.main_keyboard.append(
            [
                Button(
                    button_id='open_formatters_list',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$open_formatters_list', language),
                        callback_data=cbs.OpenMenu(
                            menu_id=MenuIds.formatters_list,
                            history=callback_data.as_history()
                            if callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ]
        )

        menu.main_keyboard.insert(
            1,
            [
                Button(
                    button_id='open_current_chat_notifications',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$telegram_notifications', language),
                        callback_data=cbs.OpenMenu(
                            menu_id=MenuIds.tg_chat_notifications,
                            history=callback_data.as_history()
                            if callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ],
        )
        return menu


class AddFormattersListButtonModification:
    @staticmethod
    async def filter(ctx: PropertiesMenuContext, menu: Menu) -> bool:
        return (
            ctx.entry.matches_path(['auto_response', '*', 'response_text'])
            or ctx.entry.matches_path(['review_reply', '*', 'review_reply_text'])
            or ctx.entry.matches_path(['review_reply', '*', 'chat_reply_text'])
        )

    @staticmethod
    async def modification(
        ctx: PropertiesMenuContext,
        menu: Menu,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Menu:
        language = properties.general.language.real_value
        callback_data = ctx.callback_data

        menu.main_keyboard.append(
            [
                Button(
                    button_id='open_formatters_list',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$open_formatters_list', language),
                        callback_data=cbs.OpenMenu(
                            menu_id=MenuIds.formatters_list,
                            history=callback_data.as_history()
                            if callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ]
        )
        return menu


class AddCommandButtonModification:
    @staticmethod
    async def filter(ctx: PropertiesMenuContext, menu: Menu) -> bool:
        return ctx.entry.matches_path(['auto_response'])

    @staticmethod
    async def modification(ctx: PropertiesMenuContext, menu: Menu) -> Menu:
        menu.footer_keyboard.append(
            [
                Button(
                    button_id='add_command',
                    obj=InlineKeyboardButton(
                        text='$add_command',
                        callback_data=cbs.Dummy().pack(),  # todo
                    ),
                ),
            ]
        )

        return menu
