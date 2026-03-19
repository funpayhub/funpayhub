from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Router

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import MenuContext
from funpayhub.lib.base_app.telegram import utils
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.first_response_cache import FirstResponseCache

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


router = Router(name='fph:first_response')
ru = translater.translate


@router.callback_query(cbs.OpenAddGreetingsToOfferMenu.filter())
async def open_menu(q: Query, state: FSM):
    msg = await MenuContext(menu_id=MenuIds.bind_first_response_to_offer, trigger=q).answer_to()
    await states.BindingGreetingsToOffer(query=q, state_message=msg).set(state)


@router.callback_query(cbs.BindGreetings.filter())
@router.message(states.BindingGreetingsToOffer.filter(), lambda msg: msg.text)
async def bind_greetings(
    obj: Query | Message,
    state: FSM,
    props: FPHProps,
    cbd: cbs.BindGreetings | None = None,
) -> Any:
    offer_id = cbd.offer_id if cbd is not None else obj.text
    if props.first_response.has_offer(offer_id):
        return obj.answer(
            ru('❌ К лоту {offer_id} уже привязан ответ на первое сообщение.', offer_id=offer_id),
            show_alert=True,
        )

    state_obj = await states.BindingGreetingsToOffer.clear(state)
    props = await props.first_response.add_for_offer(offer_id)

    await NodeMenuContext(
        menu_id=MenuIds.props_node,
        trigger=obj,
        entry_path=props.path,
        ui_history=state_obj.ui_history,
    ).answer_to(obj)
    utils.delete_message(state_obj.state_message)


@router.callback_query(cbs.RemoveGreetings.filter())
async def remove_greetings(q: Query, cbd: cbs.RemoveGreetings, props: FPHProps, tg_ui: UI) -> Any:
    node = props.first_response.detach_node(cbd.offer_id)
    if node:
        await props.save()
    await tg_ui.context_from_history(cbd.ui_history, trigger=q).apply_to()


@router.callback_query(cbs.ClearGreetingsCache.filter())
async def clear_first_response_cache(q: Query, first_response_cache: FirstResponseCache) -> Any:
    await first_response_cache.reset()
    return q.answer(ru('✅ Кэш очищен.'), show_alert=True)
