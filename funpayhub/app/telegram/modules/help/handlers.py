from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router, BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from funpayhub.lib.base_app.telegram.app.properties import callbacks as props_cbs
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from funpayhub.app.telegram.ui.ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater

    from funpayhub.app.properties import FunPayHubProperties


router = Router(name='fph:help')


need_help = set()


class NeedHelpMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data) -> None:
        if event.from_user.id not in need_help:
            await handler(event, data)
            return

        await router.propagate_event('callback_query', event, **data)


@router.message(Command('help'))
async def help_command(message: Message) -> None:
    if message.from_user.id in need_help:
        need_help.remove(message.from_user.id)
        await message.answer('Вы вышли из режима справки.')
    else:
        need_help.add(message.from_user.id)
        await message.answer('Вы вошли в режим справки. Снова введите /help для выхода.')


@router.callback_query(OpenMenu.filter())
async def show_menu_help(
    query: CallbackQuery,
    callback_data: OpenMenu,
    properties: FunPayHubProperties,
    translater: Translater,
) -> None:
    if callback_data.menu_id in [
        MenuIds.props_node,
        MenuIds.props_props,
        MenuIds.props_list_param,
        MenuIds.props_choice_param,
    ]:
        path = callback_data.context_data['entry_path']
        entry = properties.get_node(path)

        desc = translater.translate(entry.description)

        await query.answer(
            text=f'Справка:\n{desc}',
            show_alert=True,
        )


@router.callback_query(props_cbs.NextParamValue.filter())
@router.callback_query(props_cbs.ManualParamValueInput.filter())
async def show_entry_help(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: props_cbs.NextParamValue | props_cbs.ManualParamValueInput,
    translater: Translater,
) -> None:
    entry = properties.get_node(callback_data.path)
    desc = translater.translate(entry.description)

    await query.answer(
        text=f'Справка:\n{desc}',
        show_alert=True,
    )
