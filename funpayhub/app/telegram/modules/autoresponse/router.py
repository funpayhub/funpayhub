from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import StateFilter

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.base_app.telegram import utils
from funpayhub.app.telegram.ui.builders.context import StateUIContext
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from . import states, callbacks as cbs


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery as Query
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.app.main import FunPayHub as FPH
    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.lib.translater import Translater as Tr
    from funpayhub.lib.telegram.ui import UIRegistry as UI


router = r = Router(name='fph:autoresponse')


@r.callback_query(cbs.AddCommand.filter())
async def set_state(
    query: Query,
    callback_data: cbs.AddCommand,
    tg_ui: UI,
    state: FSM,
    translater: Tr,
) -> None:
    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        trigger=query,
        text=translater.translate('$add_command_message'),
        delete_on_clear=False,
        open_previous_on_clear=True,
    ).build_and_apply(tg_ui, query.message)

    await states.AddingCommand(message=msg, callback_data=callback_data).set(state)


@r.message(StateFilter(states.AddingCommand.identifier), lambda msg: msg.text)
async def add_command(
    message: Message,
    properties: FPHProps,
    hub: FPH,
    tg_ui: UI,
    state: FSM,
    translater: Tr,
) -> None:
    data = await states.AddingCommand.get(state)

    if message.text in properties.auto_response.entries:
        await message.answer(text=translater.translate('$command_exists'))
        return

    await state.clear()
    entry = properties.auto_response.add_entry(message.text)
    await properties.auto_response.save(same_file_only=True)
    await hub.emit_node_attached_event(entry)

    await NodeMenuContext(
        trigger=message,
        menu_id=MenuIds.props_node,
        entry_path=entry.path,
        callback_override=data.callback_data.copy_history(
            OpenMenu(menu_id=MenuIds.props_node, context_data={'entry_path': entry.path}),
        ),
    ).build_and_answer(tg_ui, data.message)

    asyncio.create_task(utils.delete_message(data.message))


@r.callback_query(cbs.RemoveCommand.filter())
async def delete_command(
    query: Query,
    properties: FPHProps,
    callback_data: cbs.RemoveCommand,
    translater: Tr,
    tg_ui: UI,
) -> None:
    if callback_data.command not in properties.auto_response.entries:
        await query.answer(translater.translate('$err_command_does_not_exist'), show_alert=True)
        return

    properties.auto_response.detach_node(callback_data.command)
    await properties.auto_response.save()

    await NodeMenuContext(
        trigger=query,
        menu_id=MenuIds.props_node,
        entry_path=properties.auto_response.path,
        callback_override=OpenMenu(
            menu_id=MenuIds.props_node,
            context_data={'entry_path': properties.auto_response.path},
            #  * > список команд > меню настроек команды
            history=callback_data.history[:-2],
        ),
    ).build_and_apply(tg_ui, query.message)
