from __future__ import annotations

import re
from typing import TYPE_CHECKING
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import Command, StateFilter

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties import ChoiceParameter, ToggleParameter, MutableParameter
from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.states import ChangingPage, ChangingParameterValueState
from funpayhub.lib.telegram.keyboards import clear_state_keyboard
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer

from funpayhub.lib.telegram.ui.registry import UIRegistry
from funpayhub.lib.telegram.ui.types import PropertiesUIContext
from typing import Any

from .router import router as r


if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties
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
    data: dict[str, Any]
) -> None:
    ctx = PropertiesUIContext(
        translater=translater,
        language=properties.general.language.value,
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=0,
        current_callback=cbs.MenuParamValueInput(path=properties.path).pack(),
        callbacks_history=[],
        entry=properties
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
    data: dict[str, Any]
):
    unpacked = cbs.MenuParamValueInput.unpack(query.data)

    ctx = PropertiesUIContext(
        translater=translater,
        language=properties.general.language.value,
        max_elements_on_page=properties.telegram.appearance.menu_entries_amount.value,
        page=unpacked.page,
        current_callback=query.data,
        callbacks_history=callbacks_history,
        entry=properties.get_entry(unpacked.path)
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
    bot
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
    bot
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


@r.callback_query(cbs.OpenChoiceParameter.filter())
async def open_parameter_choice(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
    parameter: ChoiceParameter,
):
    unpacked = cbs.OpenChoiceParameter.unpack(query.data)
    text, kb = menu_renderer.build_choice_parameter_menu(
        param=parameter,
        page_index=unpacked.page,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )

    await query.message.edit_text(text=text, reply_markup=kb)


@r.callback_query(cbs.ToggleParameter.filter())
async def toggle_parameter(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
    parameter: ToggleParameter,
) -> None:
    unpacked = cbs.ToggleParameter.unpack(query.data)

    parameter.toggle(save=True)

    text, keyboard = menu_renderer.build_properties_menu(
        properties=parameter.parent,
        page_index=unpacked.page,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )

    await query.message.edit_text(text, reply_markup=keyboard)


@r.callback_query(cbs.ChangeParameter.filter())
async def change_parameter_value(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    bot: Bot,
    dispatcher: Dispatcher,
    menu_renderer: TelegramPropertiesMenuRenderer,
    translater: Translater,
    parameter: MutableParameter,
) -> None:
    unpacked = cbs.ChangeParameter.unpack(query.data)

    text = translater.translate(
        '$enter_new_value_message',
        language=hub_properties.general.language.real_value(),
    ).format(
        parameter_name=parameter.name,
        parameter_description=parameter.description,
        current_parameter_value=str(parameter.value),
    )

    kb = clear_state_keyboard()
    menu_renderer.process_keyboard(
        kb,
        language=hub_properties.general.language.real_value(),
    )

    message = await bot.send_message(
        chat_id=query.message.chat.id,
        message_thread_id=query.message.message_thread_id,
        text=text,
        reply_markup=kb,
    )

    context = _get_context(dispatcher, bot, query)
    await context.clear()
    await context.set_state(ChangingParameterValueState.name)
    await context.set_data(
        {
            'data': ChangingParameterValueState(
                parameter=parameter,
                page=unpacked.page,
                menu_message=query.message,
                message=message,
                user_messages=[],
            ),
        },
    )
    await query.answer()


@r.callback_query(cbs.SelectParameterValue.filter())
async def select_parameter_value(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
    parameter: ChoiceParameter,
):
    unpacked = cbs.SelectParameterValue.unpack(query.data)
    parameter.set_value(value=unpacked.index)

    text, keyboard = menu_renderer.build_choice_parameter_menu(
        param=parameter,
        page_index=unpacked.page,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )

    await query.message.edit_text(text, reply_markup=keyboard)


@r.callback_query(cbs.SelectPage.filter())
async def change_page(
    query: CallbackQuery,
    bot: Bot,
    dispatcher: Dispatcher,
    menu_renderer: TelegramPropertiesMenuRenderer,
    hub_properties: FunPayHubProperties,
) -> None:
    state = _get_context(dispatcher, bot, query)
    await state.clear()

    kb = clear_state_keyboard()
    menu_renderer.process_keyboard(kb, hub_properties.general.language.real_value())

    msg = await bot.send_message(
        chat_id=query.message.chat.id,
        message_thread_id=query.message.message_thread_id,
        text='$enter_new_page_index_message',
        reply_markup=kb,
    )

    await state.set_state(ChangingPage.name)
    await state.set_data(
        {
            'data': ChangingPage(
                query=query,
                unpacked_query=cbs.SelectPage.unpack(query.data),
                message=msg,
                user_messages=[],
            ),
        },
    )
    await query.answer()


@r.message(StateFilter(ChangingPage.name))
async def update_page(message: Message, dispatcher: Dispatcher, bot: Bot):
    await _delete_message(message)

    if not message.text.isnumeric():
        return
    new_page_index = int(message.text) - 1

    context = _get_context(dispatcher, bot, message)
    data: ChangingPage = (await context.get_data())['data']

    if new_page_index > data.unpacked_query.pages_amount - 1 or new_page_index < 0:
        return

    await context.clear()

    await _delete_message(data.message)

    new_query = re.sub(
        r'page-\d+',
        f'page-{new_page_index}',
        data.unpacked_query.query,
    )

    event = data.query.model_copy(update={'data': new_query})
    await dispatcher.feed_update(bot=bot, update=Update(update_id=0, callback_query=event))


@r.message(StateFilter(ChangingParameterValueState.name))
async def edit_parameter(
    message: Message,
    hub_properties: FunPayHubProperties,
    bot: Bot,
    dispatcher: Dispatcher,
    menu_renderer: TelegramPropertiesMenuRenderer,
) -> None:
    await _delete_message(message)

    context = _get_context(dispatcher, bot, message)
    data: ChangingParameterValueState = (await context.get_data())['data']

    try:
        data.parameter.set_value(message.text)
        await context.clear()
    except ValueError as e:
        await data.message.edit_text(
            text=data.message.text
            + f'\n\nНе удалось изменить значение параметра {data.parameter.name}:\n\n{str(e)}',
            reply_markup=data.message.reply_markup,
        )
        return

    await _delete_message(data.message)

    text, keyboard = menu_renderer.build_properties_menu(
        properties=data.parameter.parent,
        page_index=data.page,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )

    await bot.send_message(
        chat_id=message.chat.id,
        message_thread_id=message.message_thread_id,
        text=text,
        reply_markup=keyboard,
    )

    await _delete_message(data.menu_message)
