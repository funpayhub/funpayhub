from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

from aiogram import Router

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import MenuContext
from funpayhub.lib.goods_sources import FileGoodsSource
from funpayhub.lib.base_app.telegram import utils
from funpayhub.lib.telegram.callback_data import join_callbacks
from funpayhub.lib.base_app.telegram.app.properties.ui import NodeMenuContext

from funpayhub.app.telegram.ui.ids import MenuIds

from . import (
    states,
    callbacks as cbs,
)


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery
    from aiogram.fsm.context import FSMContext as FSM

    from funpayhub.lib.telegram.ui import UIRegistry as UI
    from funpayhub.lib.goods_sources import GoodsSourcesManager as GoodsManager

    from funpayhub.app.properties import FunPayHubProperties as FPHProps
    from funpayhub.app.telegram.main import Telegram


r = router = Router(name='fph:auto_delivery')
ru = translater.translate


@router.callback_query(cbs.OpenAddAutoDeliveryRuleMenu.filter())
async def open_add_auto_delivery_rule_menu(q: CallbackQuery, state: FSM) -> None:
    """
    Открывает меню добавления правила автовыдачи и активирует состояние `AddingAutoDeliveryRule`.
    """
    msg = await MenuContext(menu_id=MenuIds.add_auto_delivery_rule, trigger=q).answer_to()
    await states.AddingAutoDeliveryRule(query=q, state_message=msg).set(state)


@router.callback_query(cbs.AddAutoDeliveryRule.filter())
async def add_rule(q: CallbackQuery, props: FPHProps, cbd: cbs.AddAutoDeliveryRule, state: FSM):
    """
    Добавляет правило автовыдачи в список параметры.
    Очищает состояние, если оно является `AddingAutoDeliveryRule`.
    Открывает меню настроек правила автовыдачи.
    """
    if cbd.rule in props.auto_delivery.entries:
        return q.answer(ru('❌ Правило уже существует.'), show_alert=True)

    await states.AddingAutoDeliveryRule.clear(state)

    entry = props.auto_delivery.add_entry(cbd.rule)
    await props.auto_delivery.save()

    await NodeMenuContext(menu_id=MenuIds.props_node, trigger=q, entry_path=entry.path).apply_to()


@router.message(states.AddingAutoDeliveryRule.filter(), lambda m: m.text)
async def add_rule_from_msg(m: Message, state: FSM, props: FPHProps):
    """
    Добавляет правило автовыдачи в список параметры.
    Очищает состояние.
    Открывает меню настроек правила автовыдачи.
    """
    if m.text in props.auto_delivery.entries:
        return m.reply(ru('<b>❌ Правило уже существует.</b>'))

    data = await states.AddingAutoDeliveryRule.get(state)
    await states.AddingAutoDeliveryRule.clear(state)

    entry = props.auto_delivery.add_entry(m.text)
    await props.auto_delivery.save()

    await NodeMenuContext(menu_id=MenuIds.props_node, trigger=m, entry_path=entry.path).answer_to()
    utils.delete_message(data.state_message)


@router.callback_query(cbs.DeleteAutoDeliveryRule.filter())
async def delete_rule(q: CallbackQuery, props: FPHProps, cbd: cbs.DeleteAutoDeliveryRule) -> None:
    if cbd.rule not in props.auto_delivery.entries:
        await q.answer(ru('❌ Правило не найдено'), show_alert=True)
        return

    props.auto_delivery.detach_node(cbd.rule)
    await props.auto_delivery.save()

    await NodeMenuContext(
        trigger=q,
        menu_id=MenuIds.props_node,
        entry_path=props.auto_delivery.path,
        ui_history=cbd.ui_history[:-1],
    ).apply_to()


@router.callback_query(cbs.AutoDeliveryOpenGoodsSourcesList.filter())
async def open_bind_goods_menu(
    q: CallbackQuery,
    cbd: cbs.AutoDeliveryOpenGoodsSourcesList,
    props: FPHProps,
    state: FSM,
) -> None:
    await NodeMenuContext(
        trigger=q,
        menu_id=MenuIds.autodelivery_goods_sources_list,
        entry_path=props.auto_delivery.get_properties([cbd.rule]).path,
    ).apply_to()

    await states.BindingGoodsSource(query=q, rule=cbd.rule).set(state)


@router.callback_query(cbs.BindGoodsSourceToAutoDelivery.filter())
async def bind_goods_source(
    q: CallbackQuery,
    cbd: cbs.BindGoodsSourceToAutoDelivery,
    props: FPHProps,
    state: FSM,
    goods_manager: GoodsManager,
    tg: Telegram,
) -> None:
    source = goods_manager.get(cbd.source_id)
    if source is None:
        await q.answer(ru('❌ Источник товаров не найден.'), show_alert=True)
        return

    await states.BindingGoodsSource.clear(state)

    await (
        props.auto_delivery.get_properties([cbd.rule])
        .get_parameter(['goods_source'])
        .set_value(cbd.source_id)
    )

    await tg.fake_query(join_callbacks(*cbd.history[:-1]), q)


INVALID_CHARS = set('<>:"/\\|?*\0')  # todo: code duplicate


@router.message(states.BindingGoodsSource.filter(), lambda msg: msg.text)
async def handler(
    m: Message, state: FSM, goods_manager: GoodsManager, props: FPHProps, tg_ui: UI
) -> None:
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
            await m.reply(ru('❌ Невалидное имя файла.'))
            return
        if not filename.endswith('.txt'):
            filename += '.txt'
        source = await goods_manager.add_source(FileGoodsSource, Path('storage/goods') / filename)

    state_obj: states.BindingGoodsSource = (await state.get_data())['data']
    await (
        props.auto_delivery.get_properties([state_obj.rule])
        .get_parameter(['goods_source'])
        .set_value(source.source_id)
    )

    await state.clear()
    utils.delete_message(m)

    await NodeMenuContext(
        trigger=m,
        menu_id=MenuIds.props_node,
        entry_path=props.auto_delivery.get_properties([state_obj.rule]).path,
        ui_history=state_obj.ui_history,
    ).build_and_answer(tg_ui, m)
    await state_obj.query.message.delete()
