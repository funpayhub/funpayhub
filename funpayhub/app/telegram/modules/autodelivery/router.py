from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

from aiogram import Router

from funpayhub.lib.translater import translater
from funpayhub.lib.telegram.ui import MenuContextModel
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
async def open_add_auto_delivery_rule_menu(query: CallbackQuery, state: FSM) -> None:
    """
    Открывает меню добавления правила автовыдачи и активирует состояние `AddingAutoDeliveryRule`.
    """
    await query.answer()
    msg = await MenuContextModel(
        menu_id=MenuIds.add_auto_delivery_rule,
        trigger=query,
    ).answer_to(query.message)

    await states.AddingAutoDeliveryRule(query=query, state_message=msg).set(state)


@router.callback_query(cbs.AddAutoDeliveryRule.filter())
async def add_rule(
    query: CallbackQuery,
    properties: FPHProps,
    callback_data: cbs.AddAutoDeliveryRule,
    state: FSM,
) -> None:
    """
    Добавляет правило автовыдачи в список параметры.
    Очищает состояние, если оно является `AddingAutoDeliveryRule`.
    Открывает меню настроек правила автовыдачи.
    """
    if callback_data.rule in properties.auto_delivery.entries:
        await query.answer(ru('❌ Правило уже существует.'), show_alert=True)
        return

    await states.AddingAutoDeliveryRule.clear(state)

    entry = properties.auto_delivery.add_entry(callback_data.rule)
    await properties.auto_delivery.save()

    await NodeMenuContext(
        trigger=query,
        menu_id=MenuIds.props_node,
        entry_path=entry.path,
    ).apply_to(query.message)


@router.message(states.AddingAutoDeliveryRule.filter(), lambda msg: msg.text)
async def add_rule_from_msg(msg: Message, state: FSM, properties: FPHProps) -> None:
    """
    Добавляет правило автовыдачи в список параметры.
    Очищает состояние.
    Открывает меню настроек правила автовыдачи.
    """
    if msg.text in properties.auto_delivery.entries:
        await msg.reply(translater.translate('❌ Правило уже существует.'))
        return

    data = await states.AddingAutoDeliveryRule.get(state)
    await states.AddingAutoDeliveryRule.clear(state)

    entry = properties.auto_delivery.add_entry(msg.text)
    await properties.auto_delivery.save()

    await NodeMenuContext(
        trigger=msg,
        menu_id=MenuIds.props_node,
        entry_path=entry.path,
    ).answer_to(msg)
    utils.delete_message(data.message)


@router.callback_query(cbs.DeleteAutoDeliveryRule.filter())
async def delete_auto_delivery_rule(
    query: CallbackQuery,
    properties: FPHProps,
    callback_data: cbs.DeleteAutoDeliveryRule,
) -> None:
    if callback_data.rule not in properties.auto_delivery.entries:
        await query.answer(ru('❌ Правило не найдено'), show_alert=True)
        return

    properties.auto_delivery.detach_node(callback_data.rule)
    await properties.auto_delivery.save()

    await NodeMenuContext(
        trigger=query,
        menu_id=MenuIds.props_node,
        entry_path=properties.auto_delivery.path,
        ui_history=callback_data.ui_history[:-1],
    ).apply_to(query.message)


@router.callback_query(cbs.AutoDeliveryOpenGoodsSourcesList.filter())
async def open_bind_goods_menu(
    query: CallbackQuery,
    callback_data: cbs.AutoDeliveryOpenGoodsSourcesList,
    properties: FPHProps,
    state: FSM,
) -> None:
    await NodeMenuContext(
        trigger=query,
        menu_id=MenuIds.autodelivery_goods_sources_list,
        entry_path=properties.auto_delivery.get_properties([callback_data.rule]).path,
    ).apply_to(query.message)

    await states.BindingGoodsSource(query=query, rule=callback_data.rule).set(state)


@router.callback_query(cbs.BindGoodsSourceToAutoDelivery.filter())
async def bind_goods_source(
    query: CallbackQuery,
    callback_data: cbs.BindGoodsSourceToAutoDelivery,
    properties: FPHProps,
    state: FSM,
    goods_manager: GoodsManager,
    tg: Telegram,
) -> None:
    source = goods_manager.get(callback_data.source_id)
    if source is None:
        await query.answer(ru('❌ Источник товаров не найден.'), show_alert=True)
        return

    await states.BindingGoodsSource.clear(state)

    await (
        properties.auto_delivery.get_properties([callback_data.rule])
        .get_parameter(['goods_source'])
        .set_value(callback_data.source_id)
    )

    await tg.fake_query(join_callbacks(*callback_data.history[:-1]), query)


INVALID_CHARS = set('<>:"/\\|?*\0')  # todo: code duplicate


@router.message(states.BindingGoodsSource.filter(), lambda msg: msg.text)
async def handler(
    message: Message,
    state: FSM,
    goods_manager: GoodsManager,
    properties: FPHProps,
    tg_ui: UI,
) -> None:
    for i in goods_manager._sources.values():
        if i.display_id == message.text:
            source = i
            break

    else:
        filename = message.text
        if (
            filename in ['.', '..']
            or filename.endswith((' ', '.'))
            or any(c in INVALID_CHARS for c in filename)
            or any(ord(c) < 32 for c in filename)
        ):
            await message.reply(ru('❌ Невалидное имя файла.'))
            return
        if not filename.endswith('.txt'):
            filename += '.txt'
        source = await goods_manager.add_source(FileGoodsSource, Path('storage/goods') / filename)

    state_obj: states.BindingGoodsSource = (await state.get_data())['data']
    await (
        properties.auto_delivery.get_properties([state_obj.rule])
        .get_parameter(['goods_source'])
        .set_value(source.source_id)
    )

    await state.clear()
    utils.delete_message(message)

    await NodeMenuContext(
        trigger=message,
        menu_id=MenuIds.props_node,
        entry_path=properties.auto_delivery.get_properties([state_obj.rule]).path,
        ui_history=state_obj.ui_history,
    ).build_and_answer(tg_ui, message)
    await state_obj.query.message.delete()
