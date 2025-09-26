from __future__ import annotations

from typing import TYPE_CHECKING, Any
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import Command, StateFilter

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.states import ChangingParameterValueState
from funpayhub.lib.telegram.ui.types import UIContext, PropertiesUIContext
from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.lib.telegram.callback_data import UnknownCallback, join_callbacks

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
    callback_data: cbs.OpenMenu,
    unpacked_callback: UnknownCallback
):
    context = UIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        menu_page=callback_data.menu_page,
        view_page=callback_data.view_page,
        callback=unpacked_callback,
    )

    menu = await tg_ui.build_menu(menu_id=callback_data.menu_id, ctx=context, data=data)

    await query.message.edit_text(
        text=menu.text,
        reply_markup=menu.total_keyboard(convert=True, hash=True),
    )
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


@r.message(Command('start'))
async def send_menu(
    message: Message,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    data: dict[str, Any],
) -> None:
    callback_str = cbs.OpenEntryMenu(path=properties.path)
    ctx = PropertiesUIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        callback=callback_str,
        entry=properties,
    )
    await (await tg_ui.build_properties_menu(ctx, data)).reply_to(message)


@r.callback_query(cbs.OpenEntryMenu.filter())
async def open_entry_menu(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    unpacked_callback: UnknownCallback,
    callback_data: cbs.OpenEntryMenu,
    data: dict[str, Any],
):
    ctx = PropertiesUIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        menu_page=callback_data.menu_page or 0,
        callback=unpacked_callback,
        entry=properties.get_entry(callback_data.path),
    )
    await (await tg_ui.build_properties_menu(ctx, data)).apply_to(query.message)


@r.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.NextParamValue,
    dispatcher: Dispatcher,
    bot,
):
    try:
        next(properties.get_parameter(callback_data.path))
    except Exception as e:
        await query.answer(text=str(e), show_alert=True)
        raise

    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=query.model_copy(update={'data': callback_data.pack_history()}),
        )
    )


@r.callback_query(cbs.ChooseParamValue.filter())
async def choose_param_value(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.ChooseParamValue,
    dispatcher: Dispatcher,
    bot,
):
    properties.get_parameter(callback_data.path).set_value(callback_data.choice_index)

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

    ctx = PropertiesUIContext(
        language=properties.general.language.real_value(),
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        menu_page=0,
        callback=unpacked_callback,
        entry=properties.get_parameter(callback_data.path),
    )

    msg = await (await tg_ui.build_properties_menu(ctx=ctx, data=data)).reply_to(query.message)

    await state.set_state(ChangingParameterValueState.name)
    await state.set_data(
        {
            'data': ChangingParameterValueState(
                parameter=ctx.entry,
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

    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=data.callback_query_obj.model_copy(
                update={'data': join_callbacks(*data.callbacks_history)}
            ),
        ),
    )
