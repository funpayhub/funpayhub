from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Router
from aiogram.filters import StateFilter

from funpayhub.lib.translater import translater
from funpayhub.lib.base_app.telegram import utils
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.telegram.ui.builders.context import StateUIContext

from . import (
    states,
    callbacks as cbs,
)


if TYPE_CHECKING:
    from aiogram.types import (
        Message,
        CallbackQuery as Query,
    )
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.lib.telegram.ui import UIRegistry as UI

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


router = r = Router(name='fph:autoresponse')
ru = translater.translate


@r.callback_query(cbs.AddCommand.filter())
async def set_state(q: Query, cbd: cbs.AddCommand, state: FSM) -> Any:
    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        trigger=q,
        text=ru('<b>➕ Введите команду.</b>'),
        ui_history=cbd.ui_history,
    ).answer_to()

    await states.AddingCommand(query=q, state_message=msg).set(state)


@r.message(StateFilter(states.AddingCommand.identifier), lambda msg: msg.text)
async def add_command(m: Message, props: FPHProps, state: FSM) -> Any:
    if m.text in props.auto_response.entries:
        return m.answer(text=ru('<b>❌ Команда уже существует.</b>'))

    data = await states.AddingCommand.clear(state)
    entry = await props.auto_response.add_entry(m.text)
    await props.auto_response.save(same_file_only=True)

    await NodeMenuContext(
        menu_id=MenuIds.props_node,
        trigger=m,
        entry_path=entry.path,
        ui_history=data.ui_history,
    ).answer_to()
    utils.delete_message(data.state_message)


@r.callback_query(cbs.RemoveCommand.filter())
async def delete_command(q: Query, props: FPHProps, cbd: cbs.RemoveCommand, tg_ui: UI) -> Any:
    if cbd.command not in props.auto_response.entries:
        return q.answer(ru('❌ Команда не найдена.'), show_alert=True)

    await props.auto_response.detach_node_and_emit(cbd.command)
    await props.auto_response.save()

    await tg_ui.context_from_history(cbd.ui_history[:-1], trigger=q).apply_to()
