from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Router
from aiogram.filters import StateFilter

from funpayhub.lib.exceptions import PropertiesError
from funpayhub.lib.telegram.callback_data import UnknownCallback
from funpayhub.lib.base_app.telegram.utils import delete_message
from funpayhub.lib.base_app.telegram.app.ui import callbacks as ui_cbs

from . import states, callbacks as cbs
from .ui import NodeMenuIds, NodeMenuContext


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery
    from aiogram.fsm.context import FSMContext

    from funpayhub.lib.base_app import App
    from funpayhub.lib.properties import Properties, ListParameter
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import UIRegistry
    from funpayhub.lib.base_app.telegram.main import TelegramApp


router = Router()


@router.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    query: CallbackQuery,
    properties: Properties,
    callback_data: cbs.NextParamValue,
    app: App,
) -> None:
    param = properties.get_parameter(callback_data.path)
    await param.next_value(save=True)
    await app.emit_parameter_changed_event(param)
    await app.telegram.fake_query(callback_data, query, pack_history=True)


@router.callback_query(cbs.ChooseParamValue.filter())
async def choose_param_value(
    query: CallbackQuery,
    properties: Properties,
    callback_data: cbs.ChooseParamValue,
    app: App,
) -> None:
    param = properties.get_parameter(callback_data.path)
    await param.set_value(callback_data.choice_id)
    await app.emit_parameter_changed_event(param)
    await app.telegram.fake_query(callback_data, query, pack_history=True)


@router.callback_query(cbs.ManualParamValueInput.filter())
async def change_parameter_value(
    query: CallbackQuery,
    properties: Properties,
    tg_ui: UIRegistry,
    callback_data: cbs.ManualParamValueInput,
    state: FSMContext,
) -> None:
    await state.clear()

    entry = properties.get_parameter(callback_data.path)
    msg = await NodeMenuContext(
        menu_id=NodeMenuIds.props_param_manual_input,
        trigger=query,
        entry_path=entry.path,
        callback_override=callback_data.copy_history(
            ui_cbs.OpenMenu(
                menu_id=NodeMenuIds.props_param_manual_input,
                context_data={'entry_path': entry.path},
            ),
        ),
    ).build_and_apply(tg_ui, query.message)

    state_obj = states.ChangingParameterValue(parameter=entry, query=query, message=msg)
    await state.set_state(state_obj.identifier)
    await state.set_data({'data': state_obj})


@router.message(StateFilter(states.ChangingParameterValue.identifier))
async def edit_parameter(message: Message, app: App, translater: Tr, state: FSMContext) -> None:
    await delete_message(message)

    data: states.ChangingParameterValue = (await state.get_data())['data']
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

    await app.emit_parameter_changed_event(data.parameter)
    await app.telegram.fake_query(data.callback_data, data.query, pack_history=True)


@router.callback_query(cbs.ListParamItemAction.filter())
async def make_list_item_action(
    query: CallbackQuery,
    callback_data: cbs.ListParamItemAction,
    properties: Properties,
    tg: TelegramApp,
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
        param._value[index], param._value[index - 1] = param._value[index - 1], param._value[index]
    elif callback_data.action == 'move_down':
        if index == len(param.value) - 1:
            await query.answer()
            return
        param._value[index], param._value[index + 1] = param._value[index + 1], param._value[index]

    await param.save()

    new_callback = UnknownCallback.from_string(callback_data.pack_history(hash=False))
    new_callback.data['mode'] = callback_data.action
    await tg.fake_query(new_callback.pack(hash=False), query)


@router.callback_query(cbs.ListParamAddItem.filter())
async def set_adding_list_item_state(
    query: CallbackQuery,
    properties: Properties,
    tg_ui: UIRegistry,
    callback_data: cbs.ListParamAddItem,
    state: FSMContext,
) -> None:
    entry: ListParameter[Any] = properties.get_parameter(callback_data.path)  # type: ignore
    msg = await NodeMenuContext(
        menu_id=NodeMenuIds.props_add_list_item,
        trigger=query,
        entry_path=entry.path,
    ).build_and_apply(tg_ui, query.message)

    state_obj = states.AddingListItem(parameter=entry, query=query, message=msg)
    await state.set_state(state_obj.identifier)
    await state.set_data({'data': state_obj})


@router.message(StateFilter(states.AddingListItem.identifier))
async def edit_parameter(message: Message, app: App, translater: Tr, state: FSMContext) -> None:
    await delete_message(message)

    data: states.AddingListItem = (await state.get_data())['data']
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

    await app.emit_parameter_changed_event(data.parameter)
    await app.telegram.fake_query(data.callback_data, data.query, pack_history=True)
