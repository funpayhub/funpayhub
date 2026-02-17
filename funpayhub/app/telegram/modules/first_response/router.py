from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

from funpayhub.lib.telegram.ui import UIRegistry, MenuContext
from funpayhub.lib.base_app.telegram.app.ui.callbacks import OpenMenu
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from . import (
    states,
    callbacks as cbs,
)
from ...ui.ids import MenuIds


if TYPE_CHECKING:
    from aiogram.types import CallbackQuery
    from aiogram.fsm.context import FSMContext

    from funpayhub.lib.translater import Translater as Tr

    from funpayhub.app.properties import FunPayHubProperties


router = Router(name='fph:first_response')


@router.callback_query(cbs.OpenAddFirstResponseToOfferMenu.filter())
async def open_menu(
    query: CallbackQuery,
    state: FSMContext,
    tg_ui: UIRegistry,
):
    msg = await MenuContext(
        menu_id=MenuIds.bind_first_response_to_offer,
        trigger=query,
    ).build_and_answer(tg_ui, query.message)

    await states.BindingFirstResponseToOffer(query=query, state_message=msg).set(state)
    await query.answer()


@router.callback_query(cbs.BindFirstResponseToOffer.filter())
async def bind_first_response_to_offer(
    query: CallbackQuery,
    callback_data: cbs.BindFirstResponseToOffer,
    state: FSMContext,
    properties: FunPayHubProperties,
    translater: Tr,
    tg_ui: UIRegistry,
):
    if properties.first_response.has_offer(callback_data.offer_id):
        await query.answer(
            translater.translate(
                '❌ К лоту {offer_id} уже привязан ответ на первое сообщение.'
            ).format(offer_id=callback_data.offer_id),
            show_alert=True,
        )
        return

    props = await properties.first_response.add_for_offer(callback_data.offer_id)
    await NodeMenuContext(
        trigger=query,
        menu_id=MenuIds.props_node,
        entry_path=props.path,
        callback_override=OpenMenu(
            menu_id=MenuIds.props_node,
            context_data={'entry_path': props.path},
            history=callback_data.history,
        ),
    ).build_and_apply(tg_ui, query.message)

    await states.BindingFirstResponseToOffer.clear(state)
