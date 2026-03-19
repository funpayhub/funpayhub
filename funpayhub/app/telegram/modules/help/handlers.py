from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router, BaseMiddleware
from aiogram.filters import Command

from funpayhub.lib.translater import translater
from funpayhub.lib.base_app.telegram.app.properties import callbacks as props_cbs
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu

from funpayhub.app.telegram.ui.ids import MenuIds


if TYPE_CHECKING:
    from aiogram.types import (
        Message,
        CallbackQuery as Query,
    )

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


router = Router(name='fph:help')
ru = translater.translate


need_help = set()


class NeedHelpMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Query, data) -> None:
        if event.from_user.id not in need_help:
            return await handler(event, data)
        await router.propagate_event('callback_query', event, **data)


@router.message(Command('help'))
async def help_command(m: Message) -> None:
    if m.from_user.id in need_help:
        need_help.remove(m.from_user.id)
        await m.answer(ru('<b>❔ Вы вышли из режима справки.</b>'))
    else:
        need_help.add(m.from_user.id)
        await m.answer(ru('<b>❔ Вы вошли в режим справки. Снова введите /help для выхода.</b>'))


@router.callback_query(OpenMenu.filter())
async def show_menu_help(q: Query, cbd: OpenMenu, props: FPHProps) -> None:
    if cbd.menu_id in [
        MenuIds.props_node,
        MenuIds.props_props,
        MenuIds.props_list_param,
        MenuIds.props_choice_param,
    ]:
        path = cbd.context_data['entry_path']
        entry = props.get_node(path)
        desc = translater.translate(entry.description)

        await q.answer(ext=f'Справка:\n{desc}', show_alert=True)
    else:
        await q.answer()


@router.callback_query(props_cbs.NextParamValue.filter())
@router.callback_query(props_cbs.ManualParamValueInput.filter())
async def show_entry_help(
    q: Query,
    props: FPHProps,
    cbd: props_cbs.NextParamValue | props_cbs.ManualParamValueInput,
) -> None:
    entry = props.get_node(cbd.path)
    desc = translater.translate(entry.description)

    await q.answer(text=f'Справка:\n{desc}', show_alert=True)
