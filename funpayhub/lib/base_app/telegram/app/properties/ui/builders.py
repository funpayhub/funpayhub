from __future__ import annotations

import html
from typing import TYPE_CHECKING

from aiogram.types import CopyTextButton, InlineKeyboardButton as InlineButton

from funpayhub.lib.exceptions import TranslatableException
from funpayhub.lib.properties import Properties as Props, parameter as param
from funpayhub.lib.telegram.ui import Menu, Button, MenuBuilder, ButtonBuilder, KeyboardBuilder
from funpayhub.lib.base_app.telegram.app.ui import callbacks as ui_cbs, ui_finalizers
from funpayhub.lib.base_app.properties_flags import ParameterFlags, PropertiesFlags

from .. import callbacks as cbs
from .context import NodeMenuContext as MenuCtx, NodeButtonContext as BtnCtx
from .registry import NodeMenuBuilder, NodeButtonBuilder


if TYPE_CHECKING:
    from funpayhub.lib.properties import Node
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import UIRegistry as UI


class ToggleParamButtonBuilder(ButtonBuilder, button_id='toggle_parameter', context_type=BtnCtx):
    async def build(self, ctx: BtnCtx, translater: Tr, properties: Props) -> Button:
        entry = properties.get_node(ctx.entry_path)
        if not isinstance(entry, param.ToggleParameter):
            raise TranslatableException(
                '%s is %s, not a `ToggleParameter`.',
                ctx.entry_path,
                type(entry),
            )

        return Button.callback_button(
            button_id='toggle_param',
            text=f'{"🟢" if entry.value else "🔴"} {translater.translate(entry.name)}',
            callback_data=cbs.NextParamValue(
                path=entry.path,
                from_callback=ctx.menu_render_context.callback_data,
            ).pack(),
        )


# Int / Float / String parameter
class ChangeParamValueButtonBuilder(ButtonBuilder, button_id='change_param', context_type=BtnCtx):
    async def build(self, ctx: BtnCtx, translater: Tr, properties: Props) -> Button:
        entry = properties.get_node(ctx.entry_path)

        if not entry.has_flag(ParameterFlags.PROTECT_VALUE):
            val_str = f'{str(entry.value)[:20] + ("..." if len(str(entry.value)) > 20 else "")}'
        else:
            val_str = '•' * 8 if entry.value else ''

        return Button.callback_button(
            button_id=f'param_change:{entry.path}',
            text=f'{translater.translate(entry.name)} 【 {val_str} 】',
            callback_data=cbs.ManualParamValueInput(
                path=entry.path,
                from_callback=ctx.menu_render_context.callback_data,
            ).pack(),
        )


# List / Choice / Properties
class OpenParamMenuButtonBuilder(ButtonBuilder, button_id='open_param', context_type=BtnCtx):
    async def build(self, ctx: BtnCtx, translater: Tr, properties: Props) -> Button:
        entry = properties.get_node(ctx.entry_path)

        return Button.callback_button(
            button_id=f'param_change:{entry.path}',
            text=translater.translate(entry.name),
            callback_data=ui_cbs.OpenMenu(
                menu_id=NodeMenuBuilder.menu_id,
                from_callback=ctx.menu_render_context.callback_data,
                context_data={'entry_path': entry.path},
            ).pack(),
        )


# Menus
def _entry_text(entry: Node, translater: Tr) -> str:
    return (
        f'<u><b>{translater.translate(entry.name)}</b></u>\n\n'
        f'<i>{translater.translate(entry.description)}</i>'
    )


class PropertiesMenuBuilder(MenuBuilder, menu_id='props_menu', context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, translater: Tr, tg_ui: UI, properties: Props) -> Menu:
        keyboard = KeyboardBuilder()
        entry = properties.get_properties(ctx.entry_path)
        for entry_id, sub_entry in entry.entries.items():
            # skip immutable params
            if not isinstance(sub_entry, Props | param.MutableParameter):
                continue

            if PropertiesFlags.HIDE in sub_entry.flags or ParameterFlags.HIDE in sub_entry.flags:
                continue

            try:
                button_ctx = BtnCtx(
                    button_id=NodeButtonBuilder.button_id,
                    menu_render_context=ctx,
                    entry_path=sub_entry.path,
                )
                button = await tg_ui.build_button(context=button_ctx)
            except:
                continue  # todo: err log

            keyboard.add_button(button)

        return Menu(
            main_text=_entry_text(entry, translater),
            main_keyboard=keyboard,
            finalizer=ui_finalizers.StripAndNavigationFinalizer(),
        )


class ChoiceParameterMenuBuilder(MenuBuilder, menu_id='choice_param_menu', context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, translater: Tr, properties: Props) -> Menu:
        keyboard = KeyboardBuilder()
        entry = properties.get_parameter(ctx.entry_path)
        if not isinstance(entry, param.ChoiceParameter):
            raise ValueError()

        for choice in entry.choices.values():
            name = translater.translate(choice.name)
            keyboard.add_callback_button(
                button_id=f'choice_param_value:{choice.id}:{entry.path}',
                text=f'【 {name} 】' if entry.value == choice.id else name,
                callback_data=cbs.ChooseParamValue(
                    path=entry.path,
                    choice_id=choice.id,
                    from_callback=ctx.callback_data,
                ).pack(),
            )

        return Menu(
            main_text=_entry_text(entry, translater),
            main_keyboard=keyboard,
            finalizer=ui_finalizers.StripAndNavigationFinalizer(),
        )


class ListParameterMenuBuilder(MenuBuilder, menu_id='list_param_menu', context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, translater: Tr, properties: Props) -> Menu:
        keyboard = KeyboardBuilder()
        mode = ctx.data.get('mode')
        entry = properties.get_node(ctx.entry_path)
        if not isinstance(entry, param.ListParameter):
            raise ValueError()

        texts = {'move_up': '⬆️', 'move_down': '⬇️', 'remove': '🗑️'}
        for index, val in enumerate(entry.value):
            if mode:
                keyboard.add_callback_button(
                    button_id='temp',
                    text=f'{texts[mode]} {val}' if mode in texts else str(val),
                    callback_data=cbs.ListParamItemAction(
                        item_index=index,
                        path=entry.path,
                        action=mode,
                        from_callback=ctx.callback_data,
                    ).pack(),
                )
            else:
                keyboard.add_row(
                    Button(
                        button_id='temp',
                        obj=InlineButton(text=str(val), copy_text=CopyTextButton(text=str(val))),
                    ),
                )

        mode_data = {
            'cancel': ('❌', None),
            'enable_move_up_mode': ('⬆️', 'move_up'),
            'enable_move_down_mode': ('⬇️', 'move_down'),
            'enable_remove_mode': ('🗑️', 'remove'),
        }
        buttons = []
        for button_id, (text, mode_str) in mode_data.items():
            buttons.append(
                Button.callback_button(
                    button_id=button_id,
                    text=text,
                    callback_data=ui_cbs.OpenMenu(
                        menu_id=NodeMenuBuilder.menu_id,
                        menu_page=ctx.menu_page,
                        history=ctx.callback_data.history if ctx.callback_data else [],
                        data={'mode': mode_str},
                        context_data={'entry_path': entry.path},
                    ).pack(),
                ),
            )

        if not mode:
            buttons.pop(0)

        buttons.append(
            Button.callback_button(
                button_id='add_list_item',
                text='➕',
                callback_data=cbs.ListParamAddItem(
                    path=entry.path,
                    from_callback=ctx.callback_data,
                ).pack(),
            ),
        )

        return Menu(
            main_text=_entry_text(entry, translater),
            main_keyboard=keyboard,
            footer_keyboard=KeyboardBuilder(keyboard=[buttons]),
            finalizer=ui_finalizers.StripAndNavigationFinalizer(),
        )


class ParamManualInputMenuBuilder(MenuBuilder, menu_id='param_manual_input', context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, translater: Tr, properties: Props) -> Menu:
        entry = properties.get_node(ctx.entry_path)
        text = translater.translate('$enter_new_value_message').format(
            parameter_name=translater.translate(entry.name),
            parameter_description=translater.translate(entry.description),
            current_parameter_value=html.escape(str(entry.value)),
        )

        footer_keyboard = KeyboardBuilder()
        footer_keyboard.add_callback_button(
            button_id='clear_state',
            text=translater.translate('$clear_state'),
            callback_data=ui_cbs.ClearState(
                delete_message=False,
                open_previous=True,
                history=ctx.callback_data.history if ctx.callback_data else [],
            ).pack(),
        )

        return Menu(
            main_text=text,
            footer_keyboard=footer_keyboard,
            finalizer=ui_finalizers.StripAndNavigationFinalizer(back_button=False),
        )


class AddListItemMenuBuilder(MenuBuilder, menu_id='add_list_param_item', context_type=MenuCtx):
    async def build(self, ctx: MenuCtx, translater: Tr) -> Menu:
        text = translater.translate('$enter_new_list_item_message')

        footer_keyboard = KeyboardBuilder()
        footer_keyboard.add_callback_button(
            button_id='clear_state',
            text=translater.translate('$clear_state'),
            callback_data=ui_cbs.ClearState(
                delete_message=False,
                open_previous=True,
                from_callback=ctx.callback_data,
            ).pack(),
        )

        return Menu(
            main_text=text,
            footer_keyboard=footer_keyboard,
            finalizer=ui_finalizers.StripAndNavigationFinalizer(back_button=False),
        )
