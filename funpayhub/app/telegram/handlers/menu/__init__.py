from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot, Router, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from mypy.typeanal import unknown_unpack
from aiogram.filters import Command, StateFilter

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.properties import ChoiceParameter, ToggleParameter, MutableParameter
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.menu_constructor.renderer import TelegramPropertiesMenuRenderer
from funpayhub.lib.properties.parameter.choice_parameter import Item


if TYPE_CHECKING:
    from funpayhub.app.properties.properties import FunPayHubProperties


r = Router()


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


@r.callback_query(cbs.OpenProperties.filter())
async def open_properties(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
) -> None:
    unpacked = cbs.OpenProperties.unpack(query.data)
    try:
        props = hub_properties.get_entry(unpacked.path)
    except LookupError:
        await query.answer(f'Не удалось найти меню по пути {unpacked.path}.', show_alert=True)
        return

    text, keyboard = menu_renderer.build_properties_menu(
        properties=props,
        page_index=unpacked.page,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )
    await query.message.edit_text(
        text=text,
        reply_markup=keyboard,
    )


@r.callback_query(cbs.ToggleParameter.filter())
async def toggle_parameter(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
) -> None:
    unpacked = cbs.ToggleParameter.unpack(query.data)
    try:
        param: ToggleParameter = hub_properties.get_parameter(unpacked.path)
    except LookupError:
        await query.answer(
            f'Не удалось найти переключатель по пути {unpacked.path}.', show_alert=True
        )
        return

    param.toggle(save=True)

    text, keyboard = menu_renderer.build_properties_menu(
        properties=param.parent,
        page_index=unpacked.page,
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )

    await query.message.edit_text(text, reply_markup=keyboard)


@r.callback_query(cbs.ChangeParameter.filter())
async def change_parameter_value(
    query: CallbackQuery, hub_properties: FunPayHubProperties, bot: Bot, dispatcher: Dispatcher
) -> None:
    unpacked = cbs.ChangeParameter.unpack(query.data)
    try:
        param: MutableParameter = hub_properties.get_parameter(unpacked.path)
    except LookupError:
        await query.answer(f'Не удалось найти параметр по пути {unpacked.path}.', show_alert=True)
        return

    state = dispatcher.fsm.get_context(
        bot,
        chat_id=query.message.chat.id,
        user_id=query.from_user.id,
        thread_id=query.message.message_thread_id,
    )
    await state.clear()
    await state.set_state('edit_parameter')
    await state.set_data({'path': unpacked.path, 'page': unpacked.page})

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data=cbs.Clear().pack())],
        ]
    )
    await bot.send_message(
        chat_id=query.message.chat.id,
        message_thread_id=query.message.message_thread_id,
        text=f'Введите новое значение для <b>{param.name}</b>\n\n'
        f'{param.description}\n\n'
        f'Текущее значение:\n'
        f'<b>{param.value}</b>',
        reply_markup=kb,
    )
    await query.answer()


@r.callback_query(cbs.OpenChoiceParameter.filter())
async def open_parameter_choice(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
    tr: Translater,
):
    unpacked = cbs.OpenChoiceParameter.unpack(query.data)

    try:
        param: ChoiceParameter = hub_properties.get_parameter(unpacked.path)
        ...
    except LookupError:
        await query.answer(f'Не удалось найти параметр по пути {unpacked.path}.', show_alert=True)
        return

    import math

    from funpayhub.lib.telegram.menu_constructor.builders import footer_builder

    markup = InlineKeyboardMarkup(inline_keyboard=[])

    start_point = unpacked.page * hub_properties.telegram.appearance.menu_entries_amount.value
    end_point = start_point + hub_properties.telegram.appearance.menu_entries_amount.value
    entries = param.choices[start_point:end_point]

    for index, i in enumerate(entries):
        text = f'【 {str(i)} 】' if start_point + index == param.value else str(i)
        markup.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=tr.translate_text(text, hub_properties.general.language.real_value()),
                    callback_data=cbs.SelectParameterValue(
                        path=unpacked.path, page=unpacked.page, index=start_point + index
                    ).pack(),
                ),
            ]
        )

    footer = footer_builder(
        page_index=unpacked.page,
        pages_amount=math.ceil(
            len(param.choices) / hub_properties.telegram.appearance.menu_entries_amount.value
        ),
        page_callback=cbs.OpenChoiceParameter(path=unpacked.path),
    ).inline_keyboard

    if footer:
        markup.inline_keyboard.extend(
            footer,
        )

    markup.inline_keyboard.append(
        [
            InlineKeyboardButton(
                text=f'◀️  {param.parent.name}',
                callback_data=cbs.OpenProperties(path=param.parent.path).pack(),
            ),
        ]
    )

    menu_renderer.process_keyboard(markup, hub_properties.general.language.real_value())

    await query.message.edit_text(
        text=tr.translate_text(
            f'<b><u>{param.name}</u></b>\n\n<i>{param.description}</i>',
            hub_properties.general.language.real_value(),
        ),
        reply_markup=markup,
    )


@r.callback_query(cbs.SelectParameterValue.filter())
async def select_parameter_value(
    query: CallbackQuery,
    hub_properties: FunPayHubProperties,
    menu_renderer: TelegramPropertiesMenuRenderer,
    tr: Translater,
):
    unpacked = cbs.SelectParameterValue.unpack(query.data)
    try:
        param: ChoiceParameter = hub_properties.get_parameter(unpacked.path)
        ...
    except LookupError:
        await query.answer(f'Не удалось найти параметр по пути {unpacked.path}.', show_alert=True)
        return

    param.set_value(value=unpacked.index)

    await open_parameter_choice(
        query=query.model_copy(
            update={'data': cbs.OpenChoiceParameter(path=param.path, page=unpacked.page).pack()}
        ),
        hub_properties=hub_properties,
        menu_renderer=menu_renderer,
        tr=tr,
    )


@r.callback_query(cbs.SelectPage.filter())
async def change_parameter_value(query: CallbackQuery, bot: Bot, dispatcher: Dispatcher) -> None:
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


@r.message(StateFilter('edit_parameter'))
async def edit_parameter(
    message: Message,
    hub_properties: FunPayHubProperties,
    bot: Bot,
    dispatcher: Dispatcher,
    menu_renderer: TelegramPropertiesMenuRenderer,
) -> None:
    state = dispatcher.fsm.get_context(
        bot,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        thread_id=message.message_thread_id,
    )
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
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Отмена', callback_data=cbs.Clear().pack())],
            ]
        )
        await message.answer(
            f'Не удалось изменить значение параметра {param.name}:\n\n{str(e)}',
            reply_markup=kb,
        )
        return

    await state.clear()

    text, keyboard = menu_renderer.build_properties_menu(
        properties=param.parent,
        page_index=data['page'],
        max_elements_on_page=hub_properties.telegram.appearance.menu_entries_amount.value,
        language=hub_properties.general.language.real_value(),
    )

    await bot.send_message(
        chat_id=message.chat.id,
        message_thread_id=message.message_thread_id,
        text=text,
        reply_markup=keyboard,
    )
