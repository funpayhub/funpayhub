from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Router
from aiogram.filters import StateFilter

from funpayhub.lib.exceptions import PropertiesError
from funpayhub.lib.base_app.telegram.utils import delete_message

from . import (
    states,
    callbacks as cbs,
)
from .ui import NodeMenuIds, NodeMenuContext


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.lib.base_app import App
    from funpayhub.lib.properties import (
        Properties as Props,
        ListParameter,
    )
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import UIRegistry


router = Router()


@router.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    q: CallbackQuery,
    properties: Props,
    callback_data: cbs.NextParamValue,
    app: App,
    tg_ui: UIRegistry,
) -> None:
    param = properties.get_parameter(callback_data.path)
    await param.next_value(save=True)
    await app.emit_parameter_changed_event(param)
    await tg_ui.context_from_history(callback_data.ui_history, trigger=q).build_and_apply(
        tg_ui, q.message
    )


@router.callback_query(cbs.ChooseParamValue.filter())
async def choose_param_value(
    query: CallbackQuery,
    properties: Props,
    callback_data: cbs.ChooseParamValue,
    tg_ui: UIRegistry,
    app: App,
) -> None:
    param = properties.get_parameter(callback_data.path)
    await param.set_value(callback_data.choice_id)
    await app.emit_parameter_changed_event(param)
    await tg_ui.context_from_history(callback_data.ui_history, trigger=query).build_and_apply(
        tg_ui,
        query.message,
    )


@router.callback_query(cbs.ManualParamValueInput.filter())
async def change_parameter_value(
    query: CallbackQuery,
    properties: Props,
    tg_ui: UIRegistry,
    callback_data: cbs.ManualParamValueInput,
    state: FSM,
) -> None:
    await state.clear()

    entry = properties.get_parameter(callback_data.path)
    msg = await NodeMenuContext(
        menu_id=NodeMenuIds.props_param_manual_input,
        trigger=query,
        entry_path=entry.path,
    ).build_and_answer(tg_ui, query.message)

    await states.ChangingParameterValue(parameter=entry, query=query, state_message=msg).set(state)
    await query.answer()


@router.message(StateFilter(states.ChangingParameterValue.identifier))
async def edit_parameter(
    message: Message, app: App, translater: Tr, state: FSM, tg_ui: UIRegistry
) -> None:
    data: states.ChangingParameterValue = (await state.get_data())['data']
    new_value = '' if message.text == '-' else message.text

    try:
        await data.parameter.set_value(new_value)
        await state.clear()
    except PropertiesError as e:
        error_text = e.format_args(translater.translate(e.message))
        await data.state_message.edit_text(
            text=data.state_message.html_text
            + f'\n\nНе удалось изменить значение параметра {data.parameter.name}:\n\n{error_text}',
            reply_markup=data.state_message.reply_markup,
        )
        return

    await app.emit_parameter_changed_event(data.parameter)
    await tg_ui.context_from_history(data.ui_history, trigger=message).build_and_answer(
        tg_ui, message
    )
    delete_message(data.state_message)


@router.callback_query(cbs.ListParamItemAction.filter())
async def make_list_item_action(
    query: CallbackQuery,
    callback_data: cbs.ListParamItemAction,
    properties: Props,
    tg_ui: UIRegistry,
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
    await tg_ui.context_from_history(callback_data.ui_history, trigger=query).build_and_apply(
        tg_ui, query.message
    )


@router.callback_query(cbs.ListParamAddItem.filter())
async def set_adding_list_item_state(
    query: CallbackQuery,
    properties: Props,
    tg_ui: UIRegistry,
    callback_data: cbs.ListParamAddItem,
    state: FSM,
) -> None:
    entry: ListParameter[Any] = properties.get_parameter(callback_data.path)  # type: ignore
    msg = await NodeMenuContext(
        menu_id=NodeMenuIds.props_add_list_item,
        trigger=query,
        entry_path=entry.path,
    ).build_and_answer(tg_ui, query.message)

    await states.AddingListItem(parameter=entry, query=query, state_message=msg).set(state)
    await query.answer()


@router.message(StateFilter(states.AddingListItem.identifier))
async def edit_parameter(
    message: Message, app: App, translater: Tr, state: FSM, tg_ui: UIRegistry
) -> None:
    data: states.AddingListItem = (await state.get_data())['data']
    try:
        await data.parameter.add_item(message.text)
        await data.parameter.save()
        await state.clear()
    except PropertiesError as e:
        error_text = e.format_args(translater.translate(e.message))
        await data.state_message.edit_text(
            text=data.state_message.html_text
            + f'\n\nНе удалось добавить элемент в список {data.parameter.name}:\n\n{error_text}',
            reply_markup=data.state_message.reply_markup,
        )
        return

    await app.emit_parameter_changed_event(data.parameter)
    await tg_ui.context_from_history(data.ui_history, trigger=message).build_and_answer(
        tg_ui, message
    )
    delete_message(data.state_message)
