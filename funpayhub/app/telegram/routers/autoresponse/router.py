from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.base_app.telegram import utils
from funpayhub.app.telegram.ui.builders.context import StateUIContext
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from . import callbacks as cbs
from .states import AddingCommand


if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.lib.translater import Translater
    from funpayhub.lib.telegram.ui import UIRegistry


router = r = Router(name='fph:autoresponse')


@r.callback_query(cbs.AddCommand.filter())
async def set_adding_command_state(
    query: CallbackQuery,
    callback_data: cbs.AddCommand,
    tg_ui: UIRegistry,
    state: FSMContext,
    translater: Translater,
) -> None:
    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        trigger=query,
        text=translater.translate('$add_command_message'),
        delete_on_clear=False,
        open_previous_on_clear=True,
    ).build_and_apply(tg_ui, query.message)

    await AddingCommand(message=msg, callback_data=callback_data).set(state)


@r.message(StateFilter(AddingCommand.identifier), lambda msg: msg.text)
async def add_command(
    message: Message,
    translater: Translater,
    properties: FunPayHubProperties,
    hub: FunPayHub,
    state: FSMContext,
    tg_ui: UIRegistry,
) -> None:
    asyncio.create_task(utils.delete_message(message))
    data = await AddingCommand.get(state)

    props = properties.auto_response
    if message.text in props.entries:
        await data.message.edit_text(
            text=data.message.text + '\n\n' + translater.translate('$command_exists'),
            reply_markup=data.message.reply_markup,
        )
        return

    await state.clear()
    entry = props.add_entry(message.text)
    await props.save(same_file_only=True)

    asyncio.create_task(hub.emit_node_attached_event(entry))

    await NodeMenuContext(
        trigger=message,
        menu_id=MenuIds.props_node,
        entry_path=entry.path,
        callback_override=data.callback_data.copy_history(
            OpenMenu(menu_id=MenuIds.props_node, context_data={'entry_path': entry.path}),
        ),
    ).build_and_apply(tg_ui, data.message)


@r.callback_query(cbs.RemoveCommand.filter())
async def delete_command(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.RemoveCommand,
    translater: Translater,
    tg_ui: UIRegistry,
):
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
