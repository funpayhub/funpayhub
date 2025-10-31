from __future__ import annotations

import asyncio
from typing import Literal

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import StateFilter

import funpayhub.lib.telegram.callbacks as cbs
from funpayhub.lib.telegram.states import ChangingMenuPage, ChangingViewPage
from funpayhub.lib.telegram.callback_data import CallbackData, UnknownCallback

from .. import utils
from .router import router


# Helpers
async def set_changing_page_state(
    query: CallbackQuery,
    callback_data: CallbackData,
    dp: Dispatcher,
    bot: Bot,
    type_: Literal['view', 'menu'],
):
    state = utils.get_context(dp, bot, query)
    await state.clear()

    msg = await query.message.answer(text='$enter_new_page_index_message')

    data = ChangingViewPage if type_ == 'view' else ChangingMenuPage
    await state.set_state(data.__identifier__)
    await state.set_data(
        {
            'data': data(
                callback_query_obj=query,
                callback_data=callback_data,
                message=msg,
                max_pages=callback_data.total_pages,
            ),
        },
    )
    await query.answer()


async def change_page_from_message(
    message: Message,
    dp: Dispatcher,
    bot: Bot,
    type_: Literal['view', 'menu'],
):
    await utils.delete_message(message)

    if not message.text.isnumeric():
        return
    new_page_index = int(message.text) - 1

    context = utils.get_context(dp, bot, message)
    if type_ == 'view':
        data: ChangingViewPage = (await context.get_data())['data']
    else:
        data: ChangingMenuPage = (await context.get_data())['data']

    if new_page_index > data.max_pages - 1 or new_page_index < 0:
        return

    await context.clear()
    asyncio.create_task(utils.delete_message(data.message))

    old = UnknownCallback.from_string(data.callback_data.history[-1])
    old.data['view_page' if type_ == 'view' else 'menu_page'] = new_page_index
    old.history = data.callback_data.history[:-1]

    await dp.feed_update(
        bot,
        Update(
            update_id=-1,
            callback_query=data.callback_query_obj.model_copy(update={'data': old.pack()}),
        ),
        dispatcher=dp,
    )


@router.callback_query(cbs.ChangePageTo.filter())
async def change_page(
    query: CallbackQuery,
    callback_data: cbs.ChangePageTo,
    dispatcher: Dispatcher,
    bot: Bot,
):
    old = CallbackData.parse(callback_data.history[-1])
    if callback_data.menu_page is not None:
        old.data['menu_page'] = callback_data.menu_page
    if callback_data.view_page is not None:
        old.data['view_page'] = callback_data.view_page
    old.history = callback_data.history[:-1]
    update = Update(
        update_id=-1,
        callback_query=query.model_copy(update={'data': old.pack()}),
    )
    await dispatcher.feed_update(bot, update, dispatcher=dispatcher)


@router.callback_query(cbs.ChangeMenuPageManually.filter())
async def manual_change_menu_page_activate(
    query: CallbackQuery,
    bot: Bot,
    dispatcher: Dispatcher,
    callback_data: cbs.ChangeMenuPageManually,
):
    await set_changing_page_state(query, callback_data, dispatcher, bot, 'menu')


@router.callback_query(cbs.ChangeViewPageManually.filter())
async def manual_change_view_page_activate(
    query: CallbackQuery,
    bot: Bot,
    dispatcher: Dispatcher,
    callback_data: cbs.ChangeMenuPageManually,
):
    await set_changing_page_state(query, callback_data, dispatcher, bot, 'view')


@router.message(StateFilter(ChangingMenuPage.__identifier__))
async def manual_menu_page_change(message: Message, dispatcher: Dispatcher, bot: Bot):
    await change_page_from_message(message, dispatcher, bot, 'menu')


@router.message(StateFilter(ChangingViewPage.__identifier__))
async def manual_view_page_change(message: Message, dispatcher: Dispatcher, bot: Bot):
    await change_page_from_message(message, dispatcher, bot, 'view')
