from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from copy import copy

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import StateFilter

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import UIRegistry, MenuContext
from funpayhub.app.telegram.states import AddingCommand

from .. import utils
from .router import router as r
from ...ui.ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.app import FunPayHub


@r.callback_query(cbs.AddCommand.filter())
async def set_adding_command_state(
    query: CallbackQuery,
    dispatcher: Dispatcher,
    bot: Bot,
    callback_data: cbs.AddCommand,
    tg_ui: UIRegistry,
    data: dict[str, Any],
) -> None:
    state = utils.get_context(dispatcher, bot, query)
    await state.clear()

    ctx = MenuContext(menu_id=MenuIds.add_command, trigger=query, data=copy(callback_data.data))
    msg = await (await tg_ui.build_menu(ctx, data)).apply_to(query.message)

    await state.set_state(AddingCommand.__identifier__)
    await state.set_data(
        {
            'data': AddingCommand(
                message=msg,
                callback_query_obj=query,
                callback_data=callback_data,
            ),
        },
    )


@r.message(StateFilter(AddingCommand.__identifier__))
async def add_command(
    message: Message,
    dispatcher: Dispatcher,
    bot: Bot,
    translater: Translater,
    properties: FunPayHubProperties,
    hub: FunPayHub,
) -> None:
    if not message.text:
        return

    asyncio.create_task(utils.delete_message(message))

    context = utils.get_context(dispatcher, bot, message)
    data: AddingCommand = (await context.get_data())['data']

    props = properties.auto_response
    if message.text in props.entries:
        await data.message.edit_text(
            text=data.message.text + '\n\n' + translater.translate('$command_exists'),
            reply_markup=data.message.reply_markup,
        )
        return

    entry = props.add_entry(message.text)
    props.save(same_file_only=True)

    asyncio.create_task(hub.emit_properties_attached_event(entry))
    await dispatcher.feed_update(
        bot,
        Update(
            update_id=0,
            callback_query=data.callback_query_obj.model_copy(
                update={'data': data.callback_data.pack_history(hash=False)},
            ),
        ),
    )
