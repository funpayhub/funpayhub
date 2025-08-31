from __future__ import annotations

from aiogram import Router, Bot, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from typing import TYPE_CHECKING

from funpayhub.lib.properties import ToggleParameter, MutableParameter, ChoiceParameter
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer
import funpayhub.lib.telegram.callbacks as cbs

if TYPE_CHECKING:
    from funpayhub.app.properties.properties import FunPayHubProperties


r = Router()


@r.message(Command('start'))
async def send_menu(message: Message, hub_properties: FunPayHubProperties, menu_renderer: TelegramPropertiesMenuRenderer) -> None:
    text, keyboard = menu_renderer.build_properties_menu(
        props=hub_properties,
        page_index=0,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.value,
    )

    print(keyboard.inline_keyboard)
    await message.answer(
        text=text,
        reply_markup=keyboard,
    )


@r.callback_query(cbs.Dummy.filter())
async def dummy(query: CallbackQuery) -> None:
    await query.answer()


@r.callback_query(cbs.Clear.filter())
async def clear(query: CallbackQuery, bot: Bot, dispatcher: Dispatcher) -> None:
    state = dispatcher.fsm.get_context(bot=bot, chat_id=query.message.chat.id, thread_id=query.message.message_thread_id, user_id=query.from_user.id)
    await state.clear()
    await query.message.delete()


@r.callback_query(cbs.OpenProperties.filter())
async def open_properties(query: CallbackQuery, hub_properties: FunPayHubProperties, tr: Translater) -> None:
    unpacked = cbs.OpenProperties.unpack(query.data)
    try:
        props = hub_properties.get_entry(unpacked.path)
    except LookupError:
        await query.answer(f'Не удалось найти меню по пути {unpacked.path}.', show_alert=True)
        return

    print(hub_properties.general.language.real_value())
    menu = PropertiesMenu(
        props,
        max_entries_on_page=hub_properties.telegram.appearance.menu_entries_amount.value
    ).build_menu(page_index=unpacked.page, tr=tr, lang=hub_properties.general.language.real_value())
    await query.message.edit_text(
        text=props.description,
        reply_markup=menu
    )


@r.callback_query(cbs.ToggleParameter.filter())
async def toggle_parameter(query: CallbackQuery, hub_properties: FunPayHubProperties, tr: Translater) -> None:
    unpacked = cbs.ToggleParameter.unpack(query.data)
    try:
        param: ToggleParameter = hub_properties.get_parameter(unpacked.path)
    except LookupError:
        await query.answer(f'Не удалось найти переключатель по пути {unpacked.path}.', show_alert=True)
        return

    param.toggle(save=True)

    menu = PropertiesMenu(param.properties).build_menu(page_index=unpacked.page, tr=tr, lang=hub_properties.general.language.real_value())
    await query.message.edit_text(param.properties.description, reply_markup=menu)


@r.callback_query(cbs.ChangeParameter.filter())
async def change_parameter_value(query: CallbackQuery, hub_properties: FunPayHubProperties, bot: Bot, dispatcher: Dispatcher) -> None:
    unpacked = cbs.ChangeParameter.unpack(query.data)
    try:
        param: MutableParameter = hub_properties.get_parameter(unpacked.path)
    except LookupError:
        await query.answer(f'Не удалось найти параметр по пути {unpacked.path}.', show_alert=True)
        return

    state = dispatcher.fsm.get_context(bot, chat_id=query.message.chat.id, user_id=query.from_user.id, thread_id=query.message.message_thread_id)
    await state.clear()
    await state.set_state('edit_parameter')
    await state.set_data({'path': unpacked.path, 'page': unpacked.page})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Отмена', callback_data=cbs.Clear().pack())]
    ])
    await bot.send_message(
        chat_id=query.message.chat.id,
        message_thread_id=query.message.message_thread_id,
        text=f'Введите новое значение для <b>{param.name}</b>\n\n'
             f'{param.description}\n\n'
             f'Текущее значение:\n'
             f'<b>{param.value}</b>',
        reply_markup=kb
    )
    await query.answer()


@r.callback_query(cbs.OpenChoiceParameter.filter())
async def open_parameter_choice(query: CallbackQuery, hub_properties: FunPayHubProperties):
    unpacked = cbs.OpenChoiceParameter.unpack(query.data)

    try:
        param: ChoiceParameter = hub_properties.get_parameter(unpacked.path)
        ...
    except LookupError:
        await query.answer(f'Не удалось найти параметр по пути {unpacked.path}.', show_alert=True)

    ...


@r.message(StateFilter('edit_parameter'))
async def edit_parameter(message: Message, hub_properties: FunPayHubProperties, bot: Bot, dispatcher: Dispatcher, tr: Translater) -> None:
    state = dispatcher.fsm.get_context(bot, chat_id=message.chat.id,
                                       user_id=message.from_user.id,
                                       thread_id=message.message_thread_id)
    data = await state.get_data()

    try:
        param: MutableParameter = hub_properties.get_entry(data['path'])
    except LookupError:
        await message.answer(f'Не удалось найти параметр по пути {data["path"]}.')
        await state.clear()
        return

    try:
        param.set_value(message.text)
    except ValueError as e:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data=cbs.Clear().pack())]
        ])
        await message.answer(
            f'Не удалось изменить значение параметра {param.name}:\n\n{str(e)}',
            reply_markup=kb
        )
        return

    await state.clear()

    await bot.send_message(
        chat_id=message.chat.id,
        message_thread_id=message.message_thread_id,
        text=param.parent.description,
        reply_markup=PropertiesMenu(param.parent).build_menu(page_index=data['page'], tr=tr, lang=hub_properties.general.language.real_value())
    )