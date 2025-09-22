from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import Command, StateFilter

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.states import ChangingParameterValueState
from funpayhub.lib.telegram.ui.types import PropertiesUIContext
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000

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
    translater: Translater,
    hashinator: HashinatorT1000,
    tg_ui: UIRegistry,
    data: dict[str, Any],
) -> None:
    ctx = PropertiesUIContext(
        translater=translater,
        language=properties.general.language.value,
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=0,
        current_callback=cbs.MenuParamValueInput(path=properties.path).pack(),
        callbacks_history=[],
        entry=properties,
    )

    window = await tg_ui.build_properties_ui(ctx, hashinator, data)

    await message.answer(
        text=window.text,
        reply_markup=window.keyboard,
    )


@r.callback_query(cbs.MenuParamValueInput.filter())
async def open_menu(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    translater: Translater,
    hashinator: HashinatorT1000,
    tg_ui: UIRegistry,
    callbacks_history: list[str],
    data: dict[str, Any],
):
    unpacked = cbs.MenuParamValueInput.unpack(query.data)

    ctx = PropertiesUIContext(
        translater=translater,
        language=properties.general.language.value,
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=unpacked.page,
        current_callback=query.data,
        callbacks_history=callbacks_history,
        entry=properties.get_entry(unpacked.path),
    )

    window = await tg_ui.build_properties_ui(ctx, hashinator, data)

    await query.message.edit_text(
        text=window.text,
        reply_markup=window.keyboard,
    )


@r.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callbacks_history: list[str],
    dispatcher: Dispatcher,
    bot,
):
    unpacked = cbs.NextParamValue.unpack(query.data)
    param = properties.get_parameter(unpacked.path)

    next(param)

    new_query = '->'.join(callbacks_history)
    new_event = query.model_copy(update={'data': new_query})
    update = Update(
        update_id=0,
        callback_query=new_event,
    )

    await dispatcher.feed_update(bot, update)


@r.callback_query(cbs.ChangePageTo.filter())
async def change_page(
    query: CallbackQuery,
    callbacks_history: list[str],
    dispatcher: Dispatcher,
    bot,
):
    unpacked = cbs.ChangePageTo.unpack(query.data)
    new_query = re.sub(
        r'page-\d+',
        f'page-{unpacked.page}',
        callbacks_history[-1],
    )
    callbacks_history[-1] = new_query

    new_event = query.model_copy(update={'data': '->'.join(callbacks_history)})
    update = Update(
        update_id=0,
        callback_query=new_event,
    )

    await dispatcher.feed_update(bot, update)


@r.callback_query(cbs.ManualParamValueInput.filter())
async def change_parameter_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    translater: Translater,
    hashinator: HashinatorT1000,
    tg_ui: UIRegistry,
    callbacks_history: list[str],
    data: dict[str, Any],
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    state = _get_context(dispatcher, bot, query)
    await state.clear()

    unpacked = cbs.ManualParamValueInput.unpack(query.data)
    param = properties.get_parameter(unpacked.path)

    ctx = PropertiesUIContext(
        translater=translater,
        language=properties.general.language.value,
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=0,
        current_callback=query.data,
        callbacks_history=callbacks_history,
        entry=param,
    )

    window = await tg_ui.build_properties_ui(ctx=ctx, hashinator=hashinator, data=data)

    msg = await bot.send_message(
        chat_id=query.message.chat.id,
        message_thread_id=query.message.message_thread_id,
        text=window.text,
        reply_markup=window.keyboard,
    )

    await state.set_state(ChangingParameterValueState.name)
    await state.set_data(
        {
            'data': ChangingParameterValueState(
                parameter=param,
                callback_query=query,
                callbacks_history=callbacks_history,
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
        print('ERROR')
        await data.message.edit_text(
            text=data.message.html_text
            + f'\n\nНе удалось изменить значение параметра {data.parameter.name}:\n\n{str(e)}',
            reply_markup=data.message.reply_markup,
        )
        return

    await _delete_message(data.message)

    data.callback_query.__dict__['data'] = '->'.join(data.callbacks_history)
    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=data.callback_query,
        ),
    )
