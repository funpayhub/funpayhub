from __future__ import annotations

import re
from typing import TYPE_CHECKING
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import Command, StateFilter

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties import ChoiceParameter, ToggleParameter, MutableParameter
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.states import ChangingPage, ChangingParameterValueState
from funpayhub.lib.telegram.keyboards import clear_state_keyboard
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer

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
@r.message(Command('menu'))
async def send_menu(
    message: Message,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
) -> None:
    text, keyboard = menu_renderer.build_properties_menu(
        properties=hub_properties,
        page_index=0,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@r.callback_query(cbs.OpenProperties.filter())
async def open_properties(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
    properties: Properties,
) -> None:
    unpacked = cbs.OpenProperties.unpack(query.data)
    text, keyboard = menu_renderer.build_properties_menu(
        properties=properties,
        page_index=unpacked.page,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )

    await query.message.edit_text(
        text=text,
        reply_markup=keyboard,
    )


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
