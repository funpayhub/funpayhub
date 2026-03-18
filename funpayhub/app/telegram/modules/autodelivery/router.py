from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

from aiogram import Router

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import MenuContext
from funpayhub.lib.goods_sources import FileGoodsSource
from funpayhub.lib.base_app.telegram import utils
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from funpayhub.app.telegram.ui.ids import MenuIds

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
    from funpayhub.lib.goods_sources import GoodsSourcesManager as GoodsManager

    from funpayhub.app.properties import FunPayHubProperties as FPHProps


r = router = Router(name='fph:auto_delivery')
ru = translater.translate


@router.callback_query(cbs.OpenAddAutoDeliveryRuleMenu.filter())
async def open_add_auto_delivery_rule_menu(q: Query, state: FSM):
    """
    Открывает меню добавления правила автовыдачи и активирует состояние `AddingAutoDeliveryRule`.
    """
    msg = await MenuContext(menu_id=MenuIds.add_auto_delivery_rule, trigger=q).answer_to()
    await states.AddingAutoDeliveryRule(query=q, state_message=msg).set(state)


@router.callback_query(cbs.AddAutoDeliveryRule.filter())
@router.message(states.AddingAutoDeliveryRule.filter(), lambda m: m.text)
async def add_rule(
    obj: Query | Message,
    state: FSM,
    props: FPHProps,
    cbd: cbs.AddAutoDeliveryRule | None = None,
):
    rule = cbd.rule if cbd is not None else obj.text
    if rule in props.auto_delivery.entries:
        return obj.answer(ru('❌ Правило уже существует.'), show_alert=True)

    state_obj = await states.AddingAutoDeliveryRule.clear(state)

    entry = props.auto_delivery.add_entry(rule)
    await props.auto_delivery.save()

    await NodeMenuContext(
        menu_id=MenuIds.props_node,
        trigger=obj,
        entry_path=entry.path,
        ui_history=state_obj.ui_history,
    ).answer_to()
    utils.delete_message(state_obj.state_message)


@router.callback_query(cbs.DeleteAutoDeliveryRule.filter())
async def delete_rule(q: Query, props: FPHProps, cbd: cbs.DeleteAutoDeliveryRule):
    if cbd.rule not in props.auto_delivery.entries:
        return q.answer(ru('❌ Правило не найдено'), show_alert=True)

    props.auto_delivery.detach_node(cbd.rule)
    await props.auto_delivery.save()

    await NodeMenuContext(
        menu_id=MenuIds.props_node,
        trigger=q,
        entry_path=props.auto_delivery.path,
        ui_history=cbd.ui_history[:-1],
    ).apply_to()


@router.callback_query(cbs.OpenBindGoodsMenu.filter())
async def open_bind_goods_menu(q: Query, cbd: cbs.OpenBindGoodsMenu, props: FPHProps, state: FSM):
    msg = await NodeMenuContext(
        trigger=q,
        menu_id=MenuIds.autodelivery_goods_sources_list,
        entry_path=props.auto_delivery.get_properties([cbd.rule]).path,
    ).answer_to()

    await states.BindingGoodsSource(query=q, rule=cbd.rule, state_message=msg).set(state)


@router.callback_query(cbs.BindGoodsSourceToAutoDelivery.filter())
async def bind_goods_source(
    q: Query,
    cbd: cbs.BindGoodsSourceToAutoDelivery,
    props: FPHProps,
    state: FSM,
    goods_manager: GoodsManager,
    tg_ui: UI,
):
    source = goods_manager.get(cbd.source_id)
    if source is None:
        return q.answer(ru('❌ Источник товаров не найден.'), show_alert=True)

    state_obj = await states.BindingGoodsSource.clear(state)

    await (
        props.auto_delivery.get_properties([cbd.rule])
        .get_parameter(['goods_source'])
        .set_value(cbd.source_id)
    )

    await tg_ui.context_from_history(cbd.ui_history[:-1], trigger=q).answer_to()
    utils.delete_message(state_obj.state_message)


INVALID_CHARS = set('<>:"/\\|?*\0')  # todo: code duplicate


@router.message(states.BindingGoodsSource.filter(), lambda msg: msg.text)
async def handler(m: Message, state: FSM, goods_manager: GoodsManager, props: FPHProps, tg_ui: UI):
    for i in goods_manager._sources.values():
        if i.display_id == m.text:
            source = i
            break
    else:
        filename = m.text
        if (
            filename in ['.', '..']
            or filename.endswith((' ', '.'))
            or any(c in INVALID_CHARS for c in filename)
            or any(ord(c) < 32 for c in filename)
        ):
            return m.reply(ru('<b>❌ Невалидное имя файла.</b>'))
        if not filename.endswith('.txt'):
            filename += '.txt'
        source = await goods_manager.add_source(FileGoodsSource, Path('storage/goods') / filename)

    state_obj = await states.BindingGoodsSource.clear(state)
    await (
        props.auto_delivery.get_properties([state_obj.rule])
        .get_parameter(['goods_source'])
        .set_value(source.source_id)
    )

    await tg_ui.context_from_history(state_obj.ui_history, trigger=m).answer_to()
    utils.delete_message(state_obj.state_message)
