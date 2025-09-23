from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import Command, StateFilter

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.states import ChangingPage, ChangingParameterValueState
from funpayhub.lib.telegram.ui.types import UIContext, PropertiesUIContext
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.lib.telegram.callbacks_parsing import UnpackedCallback, join_callbacks

from .router import router as r


if TYPE_CHECKING:
    from funpayhub.app.properties.properties import FunPayHubProperties


async def _delete_message(msg: Message):
    with suppress(Exception):
        await msg.delete()


def _get_context(dp: Dispatcher, bot: Bot, obj: Message | CallbackQuery):
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
    properties: FunPayHubProperties,
    unpacked_callback: UnpackedCallback,
):
    unpacked = cbs.OpenMenu.unpack(query.data)

    context = UIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=unpacked.page,
        callback=unpacked_callback,
    )

    menu = await tg_ui.build_menu(menu_id=unpacked.menu_id, ctx=context, data=data)

    await query.message.edit_text(
        text=menu.text,
        reply_markup=menu.total_keyboard(convert=True, hash=True),
    )
# TEMP


@r.callback_query(cbs.Dummy.filter())
async def dummy(query: CallbackQuery) -> None:
    await query.answer()


@r.callback_query(cbs.Clear.filter())
async def clear(query: CallbackQuery, bot: Bot, dispatcher: Dispatcher) -> None:
    context = _get_context(dispatcher, bot, query)
    await context.clear()
    await query.message.delete()


@r.message(Command('start'))
async def send_menu(
    message: Message,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    data: dict[str, Any],
) -> None:
    callback_str = cbs.OpenEntryMenu(path=properties.path).pack()
    unpacked = UnpackedCallback(
        current_callback=callback_str,
        history=[],
        data={}
    )
    ctx = PropertiesUIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=0,
        callback=unpacked,
        entry=properties,
    )

    menu = await tg_ui.build_properties_menu(ctx, data)

    await message.answer(
        text=menu.text,
        reply_markup=menu.total_keyboard(convert=True, hash=True),
    )


@r.callback_query(cbs.OpenEntryMenu.filter())
async def open_menu(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    unpacked_callback: UnpackedCallback,
    data: dict[str, Any]
):
    unpacked = cbs.OpenEntryMenu.unpack(query.data)

    ctx = PropertiesUIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=unpacked.page,
        callback=unpacked_callback,
        entry=properties.get_entry(unpacked.path),
    )

    menu = await tg_ui.build_properties_menu(ctx, data)

    await query.message.edit_text(
        text=menu.text,
        reply_markup=menu.total_keyboard(convert=True, hash=True),
    )


@r.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    unpacked_callback: UnpackedCallback,
    dispatcher: Dispatcher,
    bot,
):
    unpacked = cbs.NextParamValue.unpack(query.data)
    param = properties.get_parameter(unpacked.path)

    try:
        next(param)
    except Exception as e:
        await query.answer(text=str(e), show_alert=True)
        raise

    new_event = query.model_copy(update={'data': join_callbacks(*unpacked_callback.history)})
    update = Update(
        update_id=0,
        callback_query=new_event,
    )

    await dispatcher.feed_update(bot, update)


@r.callback_query(cbs.ChooseParamValue.filter())
async def choose_param_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    unpacked_callback: UnpackedCallback,
    dispatcher: Dispatcher,
    bot,
):
    unpacked = cbs.ChooseParamValue.unpack(query.data)
    param = properties.get_parameter(unpacked.path)

    param.set_value(unpacked.choice_index)

    new_query = join_callbacks(*unpacked_callback.history)
    new_event = query.model_copy(update={'data': new_query})
    update = Update(
        update_id=0,
        callback_query=new_event,
    )

    await dispatcher.feed_update(bot, update)


@r.callback_query(cbs.ChangePageTo.filter())
async def change_page(
    query: CallbackQuery,
    unpacked_callback: UnpackedCallback,
    dispatcher: Dispatcher,
    bot,
):
    unpacked = cbs.ChangePageTo.unpack(query.data)
    new_query = re.sub(
        r'page-\d+',
        f'page-{unpacked.page}',
        unpacked_callback.history[-1],
    )
    unpacked_callback.history[-1] = new_query
    # todo: better parsing

    new_event = query.model_copy(update={'data': join_callbacks(*unpacked_callback.history)})
    update = Update(
        update_id=0,
        callback_query=new_event,
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
    unpacked_callback: UnpackedCallback,
) -> None:
    state = _get_context(dispatcher, bot, query)
    await state.clear()

    unpacked = cbs.ManualParamValueInput.unpack(query.data)
    param = properties.get_parameter(unpacked.path)

    ctx = PropertiesUIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=0,
        callback=unpacked_callback,
        entry=param,
    )

    menu = await tg_ui.build_properties_menu(ctx=ctx, data=data)

    msg = await bot.send_message(
        chat_id=query.message.chat.id,
        message_thread_id=query.message.message_thread_id,
        text=menu.text,
        reply_markup=menu.total_keyboard(convert=True, hash=True),
    )

    await state.set_state(ChangingParameterValueState.name)
    await state.set_data(
        {
            'data': ChangingParameterValueState(
                parameter=param,
                callback_query_obj=query,
                callbacks_history=unpacked_callback.history,
                message=msg,
                user_messages=[],
            ),
        },
    )

    await query.answer()


@r.message(StateFilter(ChangingParameterValueState.name))
async def edit_parameter(
    message: Message,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    await _delete_message(message)

    context = _get_context(dispatcher, bot, message)
    data: ChangingParameterValueState = (await context.get_data())['data']

    try:
        data.parameter.set_value(message.text)
        await context.clear()
    except ValueError as e:
        await data.message.edit_text(
            text=data.message.html_text
            + f'\n\nНе удалось изменить значение параметра {data.parameter.name}:\n\n{str(e)}',
            reply_markup=data.message.reply_markup,
        )
        return

    await _delete_message(data.message)

    data.callback_query_obj.__dict__['data'] = join_callbacks(*data.callbacks_history)
    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=data.callback_query_obj,
        ),
    )


@r.callback_query(cbs.ChangePageManually.filter())
async def manual_change_page_activate(
    query: CallbackQuery,
    bot: Bot,
    dispatcher: Dispatcher,
    unpacked_callback: UnpackedCallback
):
    unpacked = cbs.ChangePageManually.unpack(query.data)
    state = _get_context(dispatcher, bot, query)
    await state.clear()

    msg = await bot.send_message(
        chat_id=query.message.chat.id,
        message_thread_id=query.message.message_thread_id,
        text='$enter_new_page_index_message',
    )

    await state.set_state(ChangingPage.name)
    await state.set_data(
        {
            'data': ChangingPage(
                callback_query_obj=query,
                callbacks_history=unpacked_callback.history,
                message=msg,
                max_pages=unpacked.total_pages,
                user_messages=[],
            ),
        },
    )
    await query.answer()


@r.message(StateFilter(ChangingPage.name))
async def manual_page_change(
    message: Message,
    dispatcher: Dispatcher,
    bot: Bot,
):
    await _delete_message(message)

    if not message.text.isnumeric():
        return
    new_page_index = int(message.text) - 1

    context = _get_context(dispatcher, bot, message)
    data: ChangingPage = (await context.get_data())['data']

    if new_page_index > data.max_pages - 1 or new_page_index < 0:
        return

    await context.clear()

    await _delete_message(data.message)

    new_query = re.sub(
        r'page-\d+',
        f'page-{new_page_index}',
        data.callbacks_history[-1],
    )
    data.callbacks_history[-1] = new_query

    new_event = data.callback_query_obj.model_copy(
        update={'data': join_callbacks(*data.callbacks_history)},
    )
    update = Update(
        update_id=0,
        callback_query=new_event,
    )

    await dispatcher.feed_update(bot, update)
