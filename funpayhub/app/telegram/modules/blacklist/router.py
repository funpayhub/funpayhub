from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

from funpayhub.lib.base_app.telegram.utils import delete_message
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from funpayhub.app.telegram.ui.builders.context import StateUIContext

from . import (
    states,
    callbacks as cbs,
)
from ...ui.ids import MenuIds


if TYPE_CHECKING:
    from aiogram.types import (
        Message,
        CallbackQuery as Query,
    )
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


router = r = Router(name='fph:blacklist')


@router.callback_query(cbs.BlockUser.filter())
async def add_user_msg(q: Query, state: FSM):
    msg = await StateUIContext(
        menu_id=MenuIds.state_menu,
        text='<b>➕ Введите имя пользователя, которого хотите добавить в черный список.</b>',
    ).answer_to(q)
    await states.BlockingUser(query=q, state_msg=msg).set(state)


@router.message(states.BlockingUser.filter())
async def add_user(m: Message, state: FSM, props: FPHProps):
    if not m.text:
        return None

    if props.black_list.get_user(m.text):
        return m.answer('<b>Данный пользователь уже в черном списке.</b>')

    data = await states.BlockingUser.clear(state)
    node = await props.black_list.add_user(m.text)
    await NodeMenuContext(
        menu_id=MenuIds.props_node,
        entry_path=node.path,
        ui_history=data.ui_history,
    ).answer_to(m)

    delete_message(data.state_msg)
