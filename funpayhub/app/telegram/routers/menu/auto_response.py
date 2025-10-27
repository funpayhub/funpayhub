from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from copy import copy
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import MenuContext
from funpayhub.lib.telegram.states import AddingCommand
from funpayhub.lib.telegram.ui.registry import UIRegistry

from .router import router as r
from ...ui.ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.app import FunPayHub


async def _delete_message(msg: Message):
    with suppress(Exception):
        await msg.delete()


def _get_context(dp: Dispatcher, bot: Bot, obj: Message | CallbackQuery) -> FSMContext:
    msg = obj if isinstance(obj, Message) else obj.message
    return dp.fsm.get_context(
        bot=bot,
        chat_id=msg.chat.id,
        thread_id=msg.message_thread_id,
        user_id=obj.from_user.id,
    )


@r.callback_query(cbs.AddCommand.filter())
async def set_adding_command_state(
    query: CallbackQuery,
    dispatcher: Dispatcher,
    bot: Bot,
    callback_data: cbs.AddCommand,
    tg_ui: UIRegistry,
    data: dict[str, Any],
):
    state = _get_context(dispatcher, bot, query)
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
        }
    )


@r.message(StateFilter(AddingCommand.__identifier__))
async def add_command(
    message: Message,
    dispatcher: Dispatcher,
    bot: Bot,
    translater: Translater,
    properties: FunPayHubProperties,
    hub: FunPayHub,
):
    if not message.text:
        return

    asyncio.create_task(_delete_message(message))

    language = properties.general.language.real_value
    context = _get_context(dispatcher, bot, message)
    data: AddingCommand = (await context.get_data())['data']

    props = properties.auto_response
    if message.text in props.entries:
        await data.message.edit_text(
            text=data.message.text + '\n\n' + translater.translate('$command_exists', language),
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
