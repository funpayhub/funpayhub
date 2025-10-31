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
from funpayhub.lib.telegram.ui.types import (
    Menu,
    Button,
    MenuBuilder,
    ButtonBuilder,
    MenuModification,
)
from funpayhub.app.telegram.ui.builders.properties_ui.context import (
    EntryMenuContext,
    EntryButtonContext,
)


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater
    from funpayhub.lib.telegram.ui.registry import UIRegistry


class ToggleParamButtonBuilder(ButtonBuilder):
    id = ButtonIds.properties_toggle_param
    context_type = EntryButtonContext

    async def build(self, ctx: EntryButtonContext, translater: Translater) -> Button:
        callback_data = ctx.menu_render_context.callback_data
        translated_name = translater.translate(ctx.entry.name)

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
class ChangeParamValueButtonBuilder(ButtonBuilder):
    id = ButtonIds.properties_change_param_value
    context_type = EntryButtonContext

    async def build(self, ctx: EntryButtonContext, translater: Translater) -> Button:
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
                text=f'{translater.translate(ctx.entry.name)} 【 {val_str} 】',
            ),
        )


# List / Choice / Properties
class OpenParamMenuButtonBuilder(ButtonBuilder):
    id = ButtonIds.properties_open_param_menu
    context_type = EntryButtonContext

    async def build(self, ctx: EntryButtonContext, translater: Translater) -> Button:
        callback_data = ctx.menu_render_context.callback_data

        return Button(
            button_id=f'param_change:{ctx.entry.path}',
            obj=InlineKeyboardButton(
                callback_data=cbs.OpenEntryMenu(
                    path=ctx.entry.path,
                    history=callback_data.as_history() if callback_data is not None else [],
                ).pack(),
                text=translater.translate(ctx.entry.name),
            ),
        )


def _entry_text(entry: Entry, translater: Translater) -> str:
    return f"""<u><b>{translater.translate(entry.name)}</b></u>

<i>{translater.translate(entry.description)}</i>
"""


# Menus
class PropertiesMenuBuilder(MenuBuilder):
    id = MenuIds.properties_properties
    context_type = EntryMenuContext

    async def build(self, ctx: EntryMenuContext, translater: Translater, tg_ui: UIRegistry) -> Menu:
        keyboard = []

        for entry_id, sub_entry in ctx.entry.entries.items():
            if not isinstance(sub_entry, Properties | MutableParameter):  # skip immutable params
                continue

            try:
                button_ctx = EntryButtonContext(
                    button_id=ButtonIds.properties_entry,
                    menu_render_context=ctx,
                    entry=sub_entry,
                )
                button = await tg_ui.build_button(context=button_ctx)
            except:
                import traceback

                print(traceback.format_exc())
                continue  # todo: err log

            keyboard.append([button])

        return Menu(
            text=_entry_text(ctx.entry, translater),
            main_keyboard=keyboard,
            finalizer=premade.StripAndNavigationFinalizer(),
        )


class ChoiceParameterMenuBuilder(MenuBuilder):
    id = MenuIds.properties_choice_param
    context_type = EntryMenuContext

    async def build(self, ctx: EntryMenuContext, translater: Translater) -> Menu:
        keyboard = []
        callback_data = ctx.callback_data

        for choice in ctx.entry.choices.values():
            name = translater.translate(choice.name)
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
                ],
            )

        return Menu(
            text=_entry_text(ctx.entry, translater),
            main_keyboard=keyboard,
            finalizer=premade.StripAndNavigationFinalizer(),
        )


class ListParameterMenuBuilder(MenuBuilder):
    id = MenuIds.properties_list_param
    context_type = EntryMenuContext

    async def build(self, ctx: EntryMenuContext, translater: Translater) -> Menu:
        keyboard = []
        mode = ctx.data.get('mode')
        callback_data = ctx.callback_data

        texts = {'move_up': '⬆️', 'move_down': '⬇️', 'remove': '🗑️'}
        for index, val in enumerate(ctx.entry.value):
            keyboard.append(
                [
                    Button(
                        button_id='temp',
                        obj=InlineKeyboardButton(
                            text=f'{texts[mode]} {val}' if mode in texts else str(val),
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
                ],
            )

        footer = [[]]
        mode_data = {
            'cancel': ('❌', None),
            'enable_move_up_mode': ('⬆️', 'move_up'),
            'enable_move_down_mode': ('⬇️', 'move_down'),
            'enable_remove_mode': ('🗑️', 'remove'),
        }
        buttons = []
        for button_id, (text, mode_str) in mode_data.items():
            buttons.append(
                Button(
                    button_id=button_id,
                    obj=InlineKeyboardButton(
                        text=text,
                        callback_data=cbs.OpenEntryMenu(
                            path=ctx.entry.path,
                            menu_page=ctx.menu_page,
                            history=callback_data.history if callback_data is not None else [],
                            data={'mode': mode_str},
                        ).pack(),
                    ),
                ),
            )
        footer[0].extend(buttons)
        if not mode:
            footer[0].pop(0)

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
            text=_entry_text(ctx.entry, translater),
            main_keyboard=keyboard,
            footer_keyboard=footer,
            finalizer=premade.StripAndNavigationFinalizer(),
        )


class ParamValueManualInputMenuBuilder(MenuBuilder):
    id = MenuIds.param_value_manual_input
    context_type = EntryMenuContext

    async def build(self, ctx: EntryMenuContext, translater: Translater) -> Menu:
        callback_data = ctx.callback_data
        text = translater.translate('$enter_new_value_message').format(
            parameter_name=translater.translate(ctx.entry.name),
            parameter_description=translater.translate(ctx.entry.description),
            current_parameter_value=html.escape(str(ctx.entry.value)),
        )

        footer_keyboard = [
            [
                Button(
                    button_id='clear_state',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$clear_state'),
                        callback_data=cbs.Clear(
                            delete_message=False,
                            open_previous=True,
                            history=callback_data.history if callback_data is not None else [],
                        ).pack(),
                    ),
                ),
            ],
        ]

        return Menu(
            text=text,
            footer_keyboard=footer_keyboard,
            finalizer=premade.StripAndNavigationFinalizer(back_button=False),
        )


class AddListItemMenuBuilder(MenuBuilder):
    id = MenuIds.add_list_item
    context_type = EntryMenuContext

    async def build(self, ctx: EntryMenuContext, translater: Translater) -> Menu:
        text = translater.translate('$enter_new_list_item_message').format()
        callback_data = ctx.callback_data

        footer_keyboard = [
            [
                Button(
                    button_id='clear_state',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$clear_state'),
                        callback_data=cbs.Clear(
                            delete_message=False,
                            open_previous=True,
                            history=callback_data.history if callback_data is not None else [],
                        ).pack(),
                    ),
                ),
            ],
        ]

        return Menu(
            text=text,
            footer_keyboard=footer_keyboard,
            finalizer=premade.StripAndNavigationFinalizer(back_button=False),
        )


# Modifications
class PropertiesMenuModification(MenuModification):
    id = 'fph:main_properties_menu_modification'

    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return ctx.menu_id == MenuIds.properties_entry and ctx.entry.matches_path([])

    async def modify(
        self,
        ctx: EntryMenuContext,
        menu: Menu,
        translater: Translater,
    ) -> Menu:
        callback_data = ctx.callback_data

        menu.main_keyboard.extend(
            [
                [
                    Button(
                        button_id='open_formatters_list',
                        obj=InlineKeyboardButton(
                            text=translater.translate('$open_formatters_list'),
                            callback_data=cbs.OpenMenu(
                                menu_id=MenuIds.formatters_list,
                                history=callback_data.as_history()
                                if callback_data is not None
                                else [],
                            ).pack(),
                        ),
                    ),
                ],
                [
                    Button(
                        button_id='open_control_ui',
                        obj=InlineKeyboardButton(
                            text=translater.translate('$control_ui'),
                            callback_data=cbs.OpenMenu(
                                menu_id=MenuIds.control,
                                history=callback_data.as_history()
                                if callback_data is not None
                                else [],
                            ).pack(),
                        ),
                    ),
                ],
            ]
        )

        menu.main_keyboard.insert(
            1,
            [
                Button(
                    button_id='open_current_chat_notifications',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$telegram_notifications'),
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


class AddFormattersListButtonModification(MenuModification):
    id = 'fph:add_formatters_list_button_modification'

    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return (
            ctx.entry.matches_path(['auto_response', '*', 'response_text'])
            or ctx.entry.matches_path(['review_reply', '*', 'review_reply_text'])
            or ctx.entry.matches_path(['review_reply', '*', 'chat_reply_text'])
        )

    async def modify(self, ctx: EntryMenuContext, menu: Menu, translater: Translater) -> Menu:
        callback_data = ctx.callback_data

        menu.main_keyboard.append(
            [
                Button(
                    button_id='open_formatters_list',
                    obj=InlineKeyboardButton(
                        text=translater.translate('$open_formatters_list'),
                        callback_data=cbs.OpenMenu(
                            menu_id=MenuIds.formatters_list,
                            history=callback_data.as_history()
                            if callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ],
        )
        return menu


class AddCommandButtonModification(MenuModification):
    id = 'fph:add_command_button_modification'

    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return ctx.entry.matches_path(['auto_response'])

    async def modify(self, ctx: EntryMenuContext, menu: Menu) -> Menu:
        callback_data = ctx.callback_data
        menu.footer_keyboard.append(
            [
                Button(
                    button_id='add_command',
                    obj=InlineKeyboardButton(
                        text='$add_command',
                        callback_data=cbs.AddCommand(
                            history=callback_data.as_history()
                            if callback_data is not None
                            else [],
                        ).pack(),
                    ),
                ),
            ],
        )

        return menu
