from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties import ListParameter
from funpayhub.lib.telegram.ui import MenuContext
from funpayhub.lib.telegram.states import AddingListItem, ChangingParameterValueState
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.lib.telegram.callback_data import UnknownCallback, join_callbacks
from funpayhub.app.telegram.ui.builders.properties_ui.context import EntryMenuContext

from .router import router as r
from ...ui.ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties.properties import FunPayHubProperties


async def _delete_message(msg: Message):
    with suppress(Exception):
        await msg.delete()


def _get_context(dp: Dispatcher, bot: Bot, obj: Message | CallbackQuery) -> FSMContext:
    msg = obj if isinstance(obj, Message) else obj.message
    return dp.fsm.get_context(
        bot=bot,
        chat_id=msg.chat.id,
        thread_id=msg.message_thread_id,
        user_id=obj.from_user.id,
    )


# TEMP
@r.callback_query(cbs.OpenMenu.filter())
async def open_custom_menu(
    query: CallbackQuery,
    tg_ui: UIRegistry,
    data: dict[str, Any],
    callback_data: cbs.OpenMenu,
):
    ctx = MenuContext(
        menu_id=callback_data.menu_id,
        menu_page=callback_data.menu_page,
        view_page=callback_data.view_page,
        trigger=query,
        data=callback_data.model_dump(mode='python', exclude={'identifier'}) | callback_data.data,
    )

    menu = await tg_ui.build_menu(ctx, data | {'query': query})
    await menu.apply_to(query.message)


@r.callback_query(cbs.OpenEntryMenu.filter())
async def open_entry_menu(
    query: CallbackQuery,
    tg_ui: UIRegistry,
    data: dict[str, Any],
    properties: FunPayHubProperties,
    callback_data: cbs.OpenEntryMenu,
):
    entry = properties.get_entry(callback_data.path)
    ctx = EntryMenuContext(
        menu_id=MenuIds.properties_entry,
        menu_page=callback_data.menu_page,
        trigger=query,
        entry=entry,
        data=callback_data.model_dump(mode='python', exclude={'identifier'}) | callback_data.data,
    )
    menu = await tg_ui.build_menu(ctx, data | {'query': query})
    await menu.apply_to(query.message)


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
) -> None:
    context = _get_context(dispatcher, bot, query)
    await context.clear()
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


@r.message(Command('start'))
async def send_menu(
    message: Message,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    data: dict[str, Any],
) -> None:
    ctx = EntryMenuContext(
        menu_id=MenuIds.properties_entry,
        trigger=message,
        entry=properties,
        data={'callback_data': cbs.OpenEntryMenu(path=[])},
    )

    await (await tg_ui.build_menu(ctx, data)).reply_to(message)


@r.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.NextParamValue,
    dispatcher: Dispatcher,
    hub: FunPayHub,
    bot,
):
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
):
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
    bot: Bot,
    dispatcher: Dispatcher,
    unpacked_callback: UnknownCallback,
    callback_data: cbs.ManualParamValueInput,
) -> None:
    state = _get_context(dispatcher, bot, query)
    await state.clear()

    entry = properties.get_parameter(callback_data.path)
    ctx = EntryMenuContext(
        menu_id=MenuIds.param_value_manual_input,
        trigger=query,
        entry=entry,
    )

    msg = await (await tg_ui.build_menu(ctx, data)).apply_to(query.message)

    await state.set_state(ChangingParameterValueState.__identifier__)
    await state.set_data(
        {
            'data': ChangingParameterValueState(
                parameter=entry,
                callback_query_obj=query,
                callbacks_history=unpacked_callback.history,
                message=msg,
                user_messages=[],
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
):
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


@r.message(StateFilter(ChangingParameterValueState.__identifier__))
async def edit_parameter(
    message: Message,
    bot: Bot,
    dispatcher: Dispatcher,
    hub: FunPayHub,
) -> None:
    await _delete_message(message)

    context = _get_context(dispatcher, bot, message)
    data: ChangingParameterValueState = (await context.get_data())['data']

    try:
        await data.parameter.set_value(message.text)
        await context.clear()
    except ValueError as e:
        await data.message.edit_text(
            text=data.message.html_text
            + f'\n\nНе удалось изменить значение параметра {data.parameter.name}:\n\n{str(e)}',
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
):
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
    bot: Bot,
    dispatcher: Dispatcher,
    callback_data: cbs.ListParamAddItem,
) -> None:
    state = _get_context(dispatcher, bot, query)
    await state.clear()

    entry = properties.get_parameter(callback_data.path)
    ctx = EntryMenuContext(
        menu_id=MenuIds.add_list_item,
        trigger=query,
        entry=entry,
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
                user_messages=[],
            ),
        },
    )


@r.message(StateFilter(AddingListItem.__identifier__))
async def edit_parameter(
    message: Message,
    bot: Bot,
    dispatcher: Dispatcher,
    hub: FunPayHub,
) -> None:
    await _delete_message(message)

    context = _get_context(dispatcher, bot, message)
    data: AddingListItem = (await context.get_data())['data']
    try:
        await data.parameter.add_item(message.text)
        await data.parameter.save()
        await context.clear()
    except ValueError as e:
        await data.message.edit_text(
            text=data.message.html_text
            + f'\n\nНе удалось добавить элемент в список {data.parameter.name}:\n\n{str(e)}',
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
