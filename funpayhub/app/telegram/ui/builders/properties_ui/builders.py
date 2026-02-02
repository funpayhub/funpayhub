from __future__ import annotations

import html
from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, CopyTextButton

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.properties import Properties, MutableParameter, parameter as param
from funpayhub.app.telegram.ui import premade
from funpayhub.app.telegram.ui.ids import MenuIds, ButtonIds
from funpayhub.lib.properties.base import Node
from funpayhub.app.properties.flags import (
    ParameterFlags,
    ParameterFlags as PropsFlags,
    PropertiesFlags,
)
from funpayhub.lib.telegram.ui.types import (
    Menu,
    Button,
    MenuBuilder,
    ButtonBuilder,
    KeyboardBuilder,
    MenuModification,
)
from funpayhub.app.telegram.ui.builders.properties_ui.context import (
    EntryMenuContext,
    EntryButtonContext,
)


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater
    from funpayhub.lib.goods_sources import GoodsSourcesManager
    from funpayhub.lib.telegram.ui.registry import UIRegistry


class ToggleParamButtonBuilder(
    ButtonBuilder,
    button_id=ButtonIds.properties_toggle_param,
    context_type=EntryButtonContext,
):
    async def build(
        self,
        ctx: EntryButtonContext,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Button:
        entry = properties.get_node(ctx.entry_path)
        if not isinstance(entry, param.ToggleParameter):
            raise ValueError()

        translated_name = translater.translate(entry.name)

        return Button.callback_button(
            button_id='toggle_param',
            text=f'{"🟢" if entry.value else "🔴"} {translated_name}',
            callback_data=cbs.NextParamValue(
                path=entry.path,
                from_callback=ctx.menu_render_context.callback_data,
            ).pack(),
        )


# Int / Float / String parameter
class ChangeParamValueButtonBuilder(
    ButtonBuilder,
    button_id=ButtonIds.properties_change_param_value,
    context_type=EntryButtonContext,
):
    async def build(
        self,
        ctx: EntryButtonContext,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Button:
        entry = properties.get_node(ctx.entry_path)

        if not entry.has_flag(PropsFlags.PROTECT_VALUE):
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
class OpenParamMenuButtonBuilder(
    ButtonBuilder,
    button_id=ButtonIds.properties_open_param_menu,
    context_type=EntryButtonContext,
):
    async def build(
        self,
        ctx: EntryButtonContext,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Button:
        entry = properties.get_node(ctx.entry_path)

        return Button.callback_button(
            button_id=f'param_change:{entry.path}',
            text=translater.translate(entry.name),
            callback_data=cbs.OpenMenu(
                menu_id=MenuIds.properties_entry,
                from_callback=ctx.menu_render_context.callback_data,
                context_data={
                    'entry_path': entry.path,
                },
            ).pack(),
        )


def _entry_text(entry: Node, translater: Translater) -> str:
    return f"""<u><b>{translater.translate(entry.name)}</b></u>

<i>{translater.translate(entry.description)}</i>
"""


# Menus
class PropertiesMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.properties_properties,
    context_type=EntryMenuContext,
):
    async def build(
        self,
        ctx: EntryMenuContext,
        translater: Translater,
        tg_ui: UIRegistry,
        properties: FunPayHubProperties,
    ) -> Menu:
        keyboard = KeyboardBuilder()
        entry = properties.get_properties(ctx.entry_path)
        for entry_id, sub_entry in entry.entries.items():
            if not isinstance(sub_entry, Properties | MutableParameter):  # skip immutable params
                continue

            if PropertiesFlags.HIDE in sub_entry.flags or ParameterFlags.HIDE in sub_entry.flags:
                continue

            try:
                button_ctx = EntryButtonContext(
                    button_id=ButtonIds.properties_entry,
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
            finalizer=premade.StripAndNavigationFinalizer(),
        )


class ChoiceParameterMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.properties_choice_param,
    context_type=EntryMenuContext,
):
    async def build(
        self,
        ctx: EntryMenuContext,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Menu:
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
            finalizer=premade.StripAndNavigationFinalizer(),
        )


class ListParameterMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.properties_list_param,
    context_type=EntryMenuContext,
):
    async def build(
        self,
        ctx: EntryMenuContext,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Menu:
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
                    ).pack()
                )
            else:
                keyboard.add_row(
                    Button(
                        button_id='temp',
                        obj=InlineKeyboardButton(
                            text=str(val),
                            copy_text=CopyTextButton(text=str(val))
                        )
                    )
                )

        footer = KeyboardBuilder(keyboard=[[]])
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
                    callback_data=cbs.OpenMenu(
                        menu_id=MenuIds.properties_entry,
                        menu_page=ctx.menu_page,
                        history=ctx.callback_data.history if ctx.callback_data is not None else [],
                        data={'mode': mode_str},
                        context_data={
                            'entry_path': entry.path,
                        },
                    ).pack(),
                ),
            )
        footer[0].extend(buttons)
        if not mode:
            footer[0].pop(0)

        footer[0].append(
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
            footer_keyboard=footer,
            finalizer=premade.StripAndNavigationFinalizer(),
        )


class ParamValueManualInputMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.param_value_manual_input,
    context_type=EntryMenuContext,
):
    async def build(
        self,
        ctx: EntryMenuContext,
        translater: Translater,
        properties: FunPayHubProperties,
    ) -> Menu:
        entry = properties.get_node(ctx.entry_path)
        callback_data = ctx.callback_data
        text = translater.translate('$enter_new_value_message').format(
            parameter_name=translater.translate(entry.name),
            parameter_description=translater.translate(entry.description),
            current_parameter_value=html.escape(str(entry.value)),
        )

        footer_keyboard = KeyboardBuilder()
        footer_keyboard.add_callback_button(
            button_id='clear_state',
            text=translater.translate('$clear_state'),
            callback_data=cbs.Clear(
                delete_message=False,
                open_previous=True,
                history=callback_data.history if callback_data is not None else [],
            ).pack(),
        )

        return Menu(
            main_text=text,
            footer_keyboard=footer_keyboard,
            finalizer=premade.StripAndNavigationFinalizer(back_button=False),
        )


class AddListItemMenuBuilder(
    MenuBuilder,
    menu_id=MenuIds.add_list_item,
    context_type=EntryMenuContext,
):
    async def build(
        self,
        ctx: EntryMenuContext,
        translater: Translater,
    ) -> Menu:
        text = translater.translate('$enter_new_list_item_message').format()
        callback_data = ctx.callback_data

        footer_keyboard = KeyboardBuilder()
        footer_keyboard.add_callback_button(
            button_id='clear_state',
            text=translater.translate('$clear_state'),
            callback_data=cbs.Clear(
                delete_message=False,
                open_previous=True,
                history=callback_data.history if callback_data is not None else [],
            ).pack(),
        )

        return Menu(
            main_text=text,
            footer_keyboard=footer_keyboard,
            finalizer=premade.StripAndNavigationFinalizer(back_button=False),
        )


# Modifications
class PropertiesMenuModification(
    MenuModification,
    modification_id='fph:main_properties_menu_modification',
):
    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return ctx.menu_id == MenuIds.properties_entry and ctx.entry_path == []

    async def modify(
        self,
        ctx: EntryMenuContext,
        menu: Menu,
        translater: Translater,
    ) -> Menu:
        menu.main_keyboard.insert(
            1,
            [
                Button.callback_button(
                    button_id='open_current_chat_notifications',
                    text=translater.translate('$telegram_notifications'),
                    callback_data=cbs.OpenMenu(
                        menu_id=MenuIds.tg_chat_notifications,
                        from_callback=ctx.callback_data,
                    ).pack(),
                ),
            ],
        )
        return menu


class AutoDeliveryPropertiesMenuModification(
    MenuModification,
    modification_id='fph:auto_delivery_properties_menu_modification',
):
    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return ctx.menu_id == MenuIds.properties_entry and ctx.entry_path == ['auto_delivery']

    async def modify(
        self,
        ctx: EntryMenuContext,
        menu: Menu,
        translater: Translater,
    ):
        menu.main_keyboard.add_callback_button(
            button_id='open_goods_sources_list',
            text=translater.translate('$goods_sources_list'),
            callback_data=cbs.OpenMenu(
                menu_id=MenuIds.goods_sources_list,
                from_callback=ctx.callback_data,
            ).pack(),
        )
        return menu


class AddFormattersListButtonModification(
    MenuModification,
    modification_id='fph:add_formatters_list_button_modification',
):
    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        if not ctx.entry_path:
            return False

        return any(
            [
                ctx.entry_path[0] == 'auto_response' and ctx.entry_path[-1] == 'response_text',
                ctx.entry_path[0] == 'review_reply' and ctx.entry_path[-1] == 'review_reply_text',
                ctx.entry_path[0] == 'review_reply' and ctx.entry_path[-1] == 'chat_reply_text',
            ],
        )

    async def modify(self, ctx: EntryMenuContext, menu: Menu, translater: Translater) -> Menu:
        if ctx.entry_path[0] == 'auto_response' and ctx.entry_path[-1] == 'response_text':
            query = 'fph:general|fph:message'
        elif any(
            [
                ctx.entry_path[0] == 'review_reply' and ctx.entry_path[-1] == 'review_reply_text',
                ctx.entry_path[0] == 'review_reply' and ctx.entry_path[-1] == 'chat_reply_text',
            ],
        ):
            query = 'fph:general|fph:order'
        else:
            query = None

        menu.footer_keyboard.add_callback_button(
            button_id='open_formatters_list',
            text=translater.translate('$open_formatters_list'),
            callback_data=cbs.OpenMenu(
                menu_id=MenuIds.formatters_list,
                new_message=True,
                data={'query': query} if query is not None else {},
            ).pack(),
        )
        return menu


class AddCommandButtonModification(
    MenuModification,
    modification_id='fph:add_command_button_modification',
):
    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return ctx.entry_path == ['auto_response']

    async def modify(self, ctx: EntryMenuContext, menu: Menu, translater: Translater) -> Menu:
        menu.footer_keyboard.add_callback_button(
            button_id='add_command',
            text=translater.translate('$add_command'),
            callback_data=cbs.AddCommand(from_callback=ctx.callback_data).pack(),
        )
        return menu


class AddOfferButtonModification(
    MenuModification,
    modification_id='fph:add_offer_button_modification',
):
    """Модификация добавляет кнопку \'Добавить правило\' в меню настроек автовыдачи."""

    async def filter(
        self,
        ctx: EntryMenuContext,
        menu: Menu,
        properties: FunPayHubProperties,
    ) -> bool:
        return ctx.entry_path == properties.auto_delivery.path

    async def modify(self, ctx: EntryMenuContext, menu: Menu, translater: Translater) -> Menu:
        btn = Button.callback_button(
            button_id='add_rule',
            text=translater.translate('$add_offer_rule'),
            callback_data=cbs.OpenAutoDeliveryRuleAction(from_callback=ctx.callback_data).pack(),
            row=True,
        )
        menu.footer_keyboard.insert(0, btn)
        return menu


class AddSourcesListAtAutoDeliveryModification(
    MenuModification,
    modification_id='fph:add_sources_list_to_auto_delivery',
):
    """
    Модификация, добавляющая список источников товаров к меню изменения параметра
        `auto_delivery.*.goods_source`.
    """

    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return (
            ctx.entry_path
            and ctx.entry_path[0] == 'auto_delivery'
            and ctx.entry_path[-1] == 'goods_source'
        )

    async def modify(
        self,
        ctx: EntryMenuContext,
        menu: Menu,
        goods_manager: GoodsSourcesManager,
    ) -> Menu:
        for source in goods_manager.values():
            menu.main_keyboard.add_callback_button(
                button_id=f'set_goods_source:{source.source_id}',
                text=source.display_id,
                callback_data=cbs.Dummy().pack(),
            )

        return menu


class AddRemoveButtonToAutoDeliveryModification(
    MenuModification,
    modification_id='fph:add_remove_button_to_auto_delivery',
):
    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == 'auto_delivery'

    async def modify(self, ctx: EntryMenuContext, menu: Menu, translater: Translater) -> Menu:
        key = f'{self.modification_id}:confirm_delete'

        if not ctx.data.get(key):
            menu.footer_keyboard.add_callback_button(
                button_id='delete',
                text=translater.translate('$delete'),
                callback_data=cbs.OpenMenu(
                    menu_id=ctx.menu_id,
                    menu_page=ctx.menu_page,
                    view_page=ctx.view_page,
                    context_data={'entry_path': ctx.entry_path},
                    data={**ctx.data, key: True},
                    history=ctx.callback_data.history if ctx.callback_data is not None else [],
                ).pack(),
            )
        else:
            menu.footer_keyboard.add_row(
                Button.callback_button(
                    button_id='confirm_delete',
                    text=translater.translate('$delete'),
                    callback_data=cbs.DeleteAutoDeliveryRule(
                        rule=ctx.entry_path[1],
                        from_callback=ctx.callback_data,
                    ).pack(),
                ),
                Button.callback_button(
                    button_id='cancel_delete',
                    text=translater.translate('$cancel'),
                    callback_data=cbs.OpenMenu(
                        menu_id=ctx.menu_id,
                        menu_page=ctx.menu_page,
                        view_page=ctx.view_page,
                        context_data={'entry_path': ctx.entry_path},
                        data={**ctx.data, key: False},
                        history=ctx.callback_data.history if ctx.callback_data is not None else [],
                    ).pack(),
                ),
            )
        return menu


class AddRemoveButtonToCommandModification(
    MenuModification,
    modification_id='fph:add_remove_button_to_command',
):
    async def filter(self, ctx: EntryMenuContext, menu: Menu) -> bool:
        return len(ctx.entry_path) == 2 and ctx.entry_path[0] == 'auto_response'

    async def modify(self, ctx: EntryMenuContext, menu: Menu, translater: Translater) -> Menu:
        key = f'{self.modification_id}:confirm_delete'

        if not ctx.data.get(key):
            menu.footer_keyboard.add_callback_button(
                button_id='delete',
                text=translater.translate('$delete'),
                callback_data=cbs.OpenMenu(
                    menu_id=ctx.menu_id,
                    menu_page=ctx.menu_page,
                    view_page=ctx.view_page,
                    context_data={'entry_path': ctx.entry_path},
                    data={**ctx.data, key: True},
                    history=ctx.callback_data.history if ctx.callback_data is not None else [],
                ).pack(),
            )
        else:
            menu.footer_keyboard.add_row(
                Button.callback_button(
                    button_id='confirm_delete',
                    text=translater.translate('$delete'),
                    callback_data=cbs.Dummy().pack(),
                ),
                Button.callback_button(
                    button_id='cancel_delete',
                    text=translater.translate('$cancel'),
                    callback_data=cbs.OpenMenu(
                        menu_id=ctx.menu_id,
                        menu_page=ctx.menu_page,
                        view_page=ctx.view_page,
                        context_data={'entry_path': ctx.entry_path},
                        data={**ctx.data, key: False},
                        history=ctx.callback_data.history if ctx.callback_data is not None else [],
                    ).pack(),
                ),
            )
        return menu