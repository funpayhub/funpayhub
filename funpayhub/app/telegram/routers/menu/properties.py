from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Update,
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.filters import Command, StateFilter, CommandStart
from aiogram.fsm.context import FSMContext

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.exceptions import PropertiesError
from funpayhub.lib.properties import ListParameter
from funpayhub.lib.telegram.ui import MenuContext
from funpayhub.app.telegram.states import AddingListItem, ChangingParameterValue
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.lib.telegram.callback_data import UnknownCallback, join_callbacks
from funpayhub.app.telegram.ui.builders.properties_ui.context import EntryMenuContext

from .router import router as r
from ...ui.ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.lib.translater import Translater
    from funpayhub.app.properties.properties import FunPayHubProperties


async def _delete_message(msg: Message) -> None:
    with suppress(Exception):
        await msg.delete()


# TEMP
@r.callback_query(cbs.OpenMenu.filter())
async def open_custom_menu(
    query: CallbackQuery,
    tg_ui: UIRegistry,
    data: dict[str, Any],
    callback_data: cbs.OpenMenu,
) -> None:
    menu_builder = tg_ui.get_menu_builder(callback_data.menu_id)
    ctx_class = menu_builder.builder.context_type
    additional_data = {**callback_data.data}

    parsed_callback: UnknownCallback = getattr(query, '__parsed__', None)
    if parsed_callback is not None:
        parsed_callback.data['new_message'] = False

    if callback_data.replace_history_with_trigger:
        fake_callback_history = cbs.DrawMenu(
            text=query.message.text,
            keyboard=cbs.DrawMenu.keyboard_from_message(query.message),
        ).pack(hash=False)

        fake_callback_data = callback_data.model_copy()
        fake_callback_data.history = [fake_callback_history]
        additional_data['callback_data'] = fake_callback_data

    ctx_instance = ctx_class(
        menu_id=callback_data.menu_id,
        menu_page=callback_data.menu_page,
        view_page=callback_data.view_page,
        trigger=query,
        data=additional_data,
        **callback_data.context_data,
    )

    menu = await tg_ui.build_menu(ctx_instance, data | {'query': query})

    if callback_data.new_message:
        await query.answer()
        await menu.answer_to(query.message)
    else:
        await menu.apply_to(query.message)


@r.callback_query(cbs.DrawMenu.filter())
async def draw_menu(
    query: CallbackQuery,
    callback_data: cbs.DrawMenu,
):
    kb_list = []
    for row in callback_data.keyboard:
        curr_row = []
        for button in row:
            curr_row.append(
                InlineKeyboardButton(
                    text=button.get('text'),
                    callback_data=button.get('callback_data'),
                    url=button.get('url'),
                ),
            )
        kb_list.append(curr_row)

    kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
    await query.message.edit_text(
        text=callback_data.text,
        reply_markup=kb,
    )


@r.message(CommandStart())
@r.message(Command('menu'))
async def send_menu(
    message: Message,
    tg_ui: UIRegistry,
    data: dict[str, Any],
) -> None:
    ctx = MenuContext(
        menu_id=MenuIds.main_menu,
        trigger=message,
        data={'callback_data': cbs.OpenMenu(menu_id=MenuIds.main_menu)},
    )

    await (await tg_ui.build_menu(ctx, data)).answer_to(message)


# TEMP


@r.callback_query(cbs.Dummy.filter())
async def dummy(query: CallbackQuery) -> None:
    await query.answer()


@r.callback_query(cbs.Clear.filter())
async def clear(
    query: CallbackQuery,
    bot: Bot,
    dispatcher: Dispatcher,
    callback_data: cbs.Clear,
    state: FSMContext,
) -> None:
    if callback_data.delete_message:
        await query.message.delete()
    elif callback_data.open_previous and callback_data.history:
        await dispatcher.feed_update(
            bot,
            Update(
                update_id=-1,
                callback_query=query.model_copy(update={'data': callback_data.pack_history()}),
            ),
        )
    await state.clear()


@r.message(Command('settings'))
async def send_menu(
    message: Message,
    tg_ui: UIRegistry,
    data: dict[str, Any],
) -> None:
    ctx = EntryMenuContext(
        menu_id=MenuIds.properties_entry,
        trigger=message,
        entry_path=[],
        data={
            'callback_data': cbs.OpenMenu(
                menu_id=MenuIds.properties_entry,
                context_data={'entry_path': []},
            ),
        },
    )

    await (await tg_ui.build_menu(ctx, data)).answer_to(message)


@r.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.NextParamValue,
    dispatcher: Dispatcher,
    hub: FunPayHub,
    bot,
) -> None:
    try:
        param = properties.get_parameter(callback_data.path)
        await param.next_value(save=True)
    except Exception as e:
        await query.answer(text=str(e), show_alert=True)
        raise

    asyncio.create_task(hub.emit_parameter_changed_event(param))
    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=query.model_copy(update={'data': callback_data.pack_history()}),
        ),
    )


@r.callback_query(cbs.ChooseParamValue.filter())
async def choose_param_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.ChooseParamValue,
    dispatcher: Dispatcher,
    hub: FunPayHub,
    bot,
) -> None:
    param = properties.get_parameter(callback_data.path)
    await param.set_value(callback_data.choice_id)
    asyncio.create_task(hub.emit_parameter_changed_event(param))

    update = Update(
        update_id=0,
        callback_query=query.model_copy(update={'data': callback_data.pack_history()}),
    )

    await dispatcher.feed_update(bot, update)


@r.callback_query(cbs.ManualParamValueInput.filter())
async def change_parameter_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    data: dict[str, Any],
    unpacked_callback: UnknownCallback,
    callback_data: cbs.ManualParamValueInput,
    state: FSMContext,
) -> None:
    await state.clear()

    entry = properties.get_parameter(callback_data.path)
    ctx = EntryMenuContext(
        menu_id=MenuIds.param_value_manual_input,
        trigger=query,
        entry_path=entry.path,
        data={
            'callback_data': cbs.OpenMenu(
                menu_id=MenuIds.param_value_manual_input,
                context_data={'entry_path': entry.path},
                history=callback_data.history,
            )
        }
    )

    msg = await (await tg_ui.build_menu(ctx, data)).apply_to(query.message)

    await state.set_state(ChangingParameterValue.__identifier__)
    await state.set_data(
        {
            'data': ChangingParameterValue(
                parameter=entry,
                callback_query_obj=query,
                callbacks_history=unpacked_callback.history,
                message=msg,
            ),
        },
    )


@r.callback_query(cbs.ToggleNotificationChannel.filter())
async def toggle_notification_channel(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.ToggleNotificationChannel,
    dispatcher: Dispatcher,
    bot: Bot,
) -> None:
    chat_identifier = f'{query.message.chat.id}.{query.message.message_thread_id}'
    param: ListParameter[Any] = properties.telegram.notifications[callback_data.channel]

    if chat_identifier in param.value:
        await param.remove_item(chat_identifier)
    else:
        await param.add_item(chat_identifier)
    await param.save()

    await dispatcher.feed_update(
        bot,
        Update(
            update_id=-1,
            callback_query=query.model_copy(update={'data': callback_data.pack_history()}),
        ),
    )


@r.message(StateFilter(ChangingParameterValue.identifier))
async def edit_parameter(
    message: Message,
    bot: Bot,
    dispatcher: Dispatcher,
    hub: FunPayHub,
    translater: Translater,
    state: FSMContext,
) -> None:
    await _delete_message(message)
    data: ChangingParameterValue = (await state.get_data())['data']
    new_value = '' if message.text == '-' else message.text
    try:
        await data.parameter.set_value(new_value)
        await state.clear()
    except PropertiesError as e:
        error_text = e.format_args(translater.translate(e.message))
        await data.message.edit_text(
            text=data.message.html_text
            + f'\n\nНе удалось изменить значение параметра {data.parameter.name}:\n\n{error_text}',
            reply_markup=data.message.reply_markup,
        )
        return

    asyncio.create_task(hub.emit_parameter_changed_event(data.parameter))
    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=data.callback_query_obj.model_copy(
                update={'data': join_callbacks(*data.callbacks_history)},
            ),
        ),
    )


@r.callback_query(cbs.ListParamItemAction.filter())
async def make_list_item_action(
    query: CallbackQuery,
    callback_data: cbs.ListParamItemAction,
    bot: Bot,
    dispatcher: Dispatcher,
    properties: FunPayHubProperties,
) -> None:
    if callback_data.action is None:
        await query.answer()
        return

    param: ListParameter = properties.get_parameter(callback_data.path)  # type: ignore
    index = callback_data.item_index
    if callback_data.action == 'remove':
        await param.pop_item(index)
    elif callback_data.action == 'move_up':
        if index == 0:
            await query.answer()
            return
        param.value[index], param.value[index - 1] = param.value[index - 1], param.value[index]
    elif callback_data.action == 'move_down':
        if index == len(param.value) - 1:
            await query.answer()
            return
        param.value[index], param.value[index + 1] = param.value[index + 1], param.value[index]

    await param.save()
    new_callback = UnknownCallback.from_string(callback_data.pack_history(hash=False))
    new_callback.data['mode'] = callback_data.action
    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=query.model_copy(update={'data': new_callback.pack()}),
        ),
    )


@r.callback_query(cbs.ListParamAddItem.filter())
async def set_adding_list_item_state(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    data: dict[str, Any],
    callback_data: cbs.ListParamAddItem,
    state: FSMContext,
) -> None:
    await state.clear()
    entry = properties.get_parameter(callback_data.path)
    ctx = EntryMenuContext(
        menu_id=MenuIds.add_list_item,
        trigger=query,
        entry_path=entry.path,
    )

    msg = await (await tg_ui.build_menu(ctx, data)).apply_to(query.message)

    await state.set_state(AddingListItem.__identifier__)
    await state.set_data(
        {
            'data': AddingListItem(
                parameter=entry,
                callback_query_obj=query,
                callback_data=callback_data,
                message=msg,
            ),
        },
    )


@r.message(StateFilter(AddingListItem.__identifier__))
async def edit_parameter(
    message: Message,
    bot: Bot,
    dispatcher: Dispatcher,
    hub: FunPayHub,
    translater: Translater,
    state: FSMContext,
) -> None:
    await _delete_message(message)

    data: AddingListItem = (await state.get_data())['data']
    try:
        await data.parameter.add_item(message.text)
        await data.parameter.save()
        await state.clear()
    except PropertiesError as e:
        error_text = e.format_args(translater.translate(e.message))
        await data.message.edit_text(
            text=data.message.html_text
            + f'\n\nНе удалось добавить элемент в список {data.parameter.name}:\n\n{error_text}',
            reply_markup=data.message.reply_markup,
        )
        return

    asyncio.create_task(hub.emit_parameter_changed_event(data.parameter))
    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=data.callback_query_obj.model_copy(
                update={'data': join_callbacks(data.callback_data.pack_history(hash=False))},
            ),
        ),
    )
