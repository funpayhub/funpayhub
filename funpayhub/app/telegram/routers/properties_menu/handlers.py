from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties import ChoiceParameter, ToggleParameter, MutableParameter
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer
from .router import router as r
from funpayhub.lib.telegram.states import ChangingParameterValueState
from funpayhub.lib.telegram.keyboards import clear_state_keyboard

if TYPE_CHECKING:
    from funpayhub.app.properties.properties import FunPayHubProperties
    from funpayhub.lib.properties import Properties


@r.callback_query(cbs.Dummy.filter())
async def dummy(query: CallbackQuery) -> None:
    await query.answer()


@r.callback_query(cbs.Clear.filter())
async def clear(query: CallbackQuery, bot: Bot, dispatcher: Dispatcher) -> None:
    state = dispatcher.fsm.get_context(
        bot=bot,
        chat_id=query.message.chat.id,
        thread_id=query.message.message_thread_id,
        user_id=query.from_user.id,
    )
    await state.clear()
    await query.message.delete()


@r.message(Command('start'))
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
    properties: Properties
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
    parameter: ChoiceParameter
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

    state = dispatcher.fsm.get_context(
        bot,
        chat_id=query.message.chat.id,
        user_id=query.from_user.id,
        thread_id=query.message.message_thread_id,
    )

    text = translater.translate(
        '$enter_new_value_message',
        language=hub_properties.general.language.real_value(),
    ).format(
        parameter_name = parameter.name,
        parameter_description = parameter.description,
        current_parameter_value = str(parameter.value),
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


    await state.clear()
    await state.set_state(ChangingParameterValueState.name)
    await state.set_data(
        {
            'data': ChangingParameterValueState(
                parameter=parameter,
                page=unpacked.page,
                menu_message=query.message,
                message=message,
                user_messages=[]
            )
        }
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
async def change_page(query: CallbackQuery, bot: Bot, dispatcher: Dispatcher) -> None:
    unpacked = cbs.SelectPage.unpack(query.data)

    state = dispatcher.fsm.get_context(
        bot,
        chat_id=query.message.chat.id,
        user_id=query.from_user.id,
        thread_id=query.message.message_thread_id,
    )
    await state.clear()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data=cbs.Clear().pack())],
        ]
    )
    msg = await bot.send_message(
        chat_id=query.message.chat.id,
        message_thread_id=query.message.message_thread_id,
        text='Введите номер страницы:',
        reply_markup=kb,
    )

    await state.set_state('select_page')
    await state.set_data(
        {'query': unpacked.query, 'menu_msg': query.message, 'msg': msg, 'callback_query': query}
    )
    await query.answer()


@r.message(StateFilter('select_page'))
async def update_page(message: Message, dispatcher: Dispatcher, bot: Bot):
    import re
    from aiogram.types import Update

    if not message.text.isnumeric():
        return

    state = dispatcher.fsm.get_context(
        bot,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        thread_id=message.message_thread_id,
    )
    data = await state.get_data()

    query = data['query']
    callback_query: CallbackQuery = data['callback_query']
    new_query = re.sub(r'page-\d+', f'page-{int(message.text) - 1}', query)

    event = callback_query.model_copy(update={'data': new_query})
    message_to_delete: Message = data['msg']

    await state.clear()

    await bot.delete_message(
        chat_id=message_to_delete.chat.id, message_id=message_to_delete.message_id
    )

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except:
        pass

    await dispatcher.feed_update(bot=bot, update=Update(update_id=0, callback_query=event))


@r.message(StateFilter(ChangingParameterValueState.name))
async def edit_parameter(
    message: Message,
    hub_properties: FunPayHubProperties,
    bot: Bot,
    dispatcher: Dispatcher,
    menu_renderer: TelegramPropertiesMenuRenderer,
) -> None:
    await message.delete()

    state = dispatcher.fsm.get_context(
        bot,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        thread_id=message.message_thread_id,
    )
    data: ChangingParameterValueState = (await state.get_data())['data']

    try:
        data.parameter.set_value(message.text)
        await state.clear()
    except ValueError as e:
        await data.message.edit_text(
            text=data.message.text +
                 f'\n\nНе удалось изменить значение параметра {data.parameter.name}:\n\n{str(e)}',
            reply_markup=data.message.reply_markup,
        )
        return

    await data.message.delete()

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

    await data.menu_message.delete()
