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
    from aiogram.types import (
        Message,
        CallbackQuery as Query,
    )
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.lib.base_app import App
    from funpayhub.lib.properties import (
        Properties as Props,
        ListParameter,
    )
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import UIRegistry as UI


router = Router()


@router.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    q: Query,
    props: Props,
    cbd: cbs.NextParamValue,
    app: App,
    tg_ui: UI,
) -> None:
    param = props.get_parameter(cbd.path)
    await param.next_value(save=True)
    await app.emit_parameter_changed_event(param)
    await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to(ui_registry=tg_ui)


@router.callback_query(cbs.ChooseParamValue.filter())
async def choose_param_value(
    q: Query,
    props: Props,
    cbd: cbs.ChooseParamValue,
    tg_ui: UI,
    app: App,
) -> None:
    param = props.get_parameter(cbd.path)
    await param.set_value(cbd.choice_id)
    await app.emit_parameter_changed_event(param)
    await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to(ui_registry=tg_ui)


@router.callback_query(cbs.ManualParamValueInput.filter())
async def change_parameter_value(
    q: Query,
    props: Props,
    tg_ui: UI,
    cbd: cbs.ManualParamValueInput,
    state: FSM,
) -> None:
    await state.clear()

    entry = props.get_parameter(cbd.path)
    msg = await NodeMenuContext(
        menu_id=NodeMenuIds.props_param_manual_input,
        trigger=q,
        entry_path=entry.path,
    ).answer_to(ui_registry=tg_ui)

    await states.ChangingParameterValue(parameter=entry, query=q, state_message=msg).set(state)


@router.message(StateFilter(states.ChangingParameterValue.identifier))
async def edit_parameter(
    m: Message,
    app: App,
    translater: Tr,
    state: FSM,
    tg_ui: UI,
) -> None:
    data: states.ChangingParameterValue = (await state.get_data())['data']
    new_value = '' if m.text == '-' else m.text

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
    await tg_ui.context_from_history(data.ui_history, trigger=m).answer_to(ui_registry=tg_ui)
    delete_message(data.state_message)


@router.callback_query(cbs.ListParamItemAction.filter())
async def list_action(q: Query, cbd: cbs.ListParamItemAction, props: Props, tg_ui: UI) -> None:
    if cbd.action is None:
        await q.answer()
        return

    param: ListParameter = props.get_parameter(cbd.path)  # type: ignore
    index = cbd.item_index
    if cbd.action == 'remove':
        await param.pop_item(index)
    elif cbd.action == 'move_up':
        if index == 0:
            await q.answer()
            return
        param._value[index], param._value[index - 1] = param._value[index - 1], param._value[index]
    elif cbd.action == 'move_down':
        if index == len(param.value) - 1:
            await q.answer()
            return
        param._value[index], param._value[index + 1] = param._value[index + 1], param._value[index]

    await param.save()
    await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to(ui_registry=tg_ui)


@router.callback_query(cbs.ListParamAddItem.filter())
async def set_adding_list_item_state(
    q: Query,
    props: Props,
    tg_ui: UI,
    cbd: cbs.ListParamAddItem,
    state: FSM,
) -> None:
    entry: ListParameter[Any] = props.get_parameter(cbd.path)  # type: ignore
    msg = await NodeMenuContext(
        menu_id=NodeMenuIds.props_add_list_item,
        trigger=q,
        entry_path=entry.path,
    ).answer_to(ui_registry=tg_ui)

    await states.AddingListItem(parameter=entry, query=q, state_message=msg).set(state)


@router.message(StateFilter(states.AddingListItem.identifier))
async def edit_parameter(
    m: Message,
    app: App,
    translater: Tr,
    state: FSM,
    tg_ui: UI,
) -> None:
    data: states.AddingListItem = (await state.get_data())['data']
    try:
        await data.parameter.add_item(m.text)
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
    await tg_ui.context_from_history(data.ui_history, trigger=m).answer_to(ui_registry=tg_ui)
    delete_message(data.state_message)
