from __future__ import annotations

from pathlib import Path
from contextlib import suppress

from aiogram.types import (
    Message,
    CallbackQuery as Query,
)
from hubplatform.i18n import I18nString
from aiogram.fsm.context import FSMContext as FSM
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager, MenuContext
from hubplatform.goods_source import FileGoodsSource
from hubplatform.app.components.telegram.menu_ids import MenuIDs
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext

from funpayhub.app.components.funpay.properties import FunPayProperties

from . import (
    states,
    callbacks as cbs,
)
from ..menu_ids import MenuIDs as ExtensionMenuIDs


r = router = Router(name='fph:auto_delivery')


@router.callback_query(cbs.OpenAddAutoDeliveryRuleMenu.filter())
async def open_add_auto_delivery_rule_menu(
    q: Query,
    state: FSM,
    ui_manager: UIManager,
    cbd: cbs.OpenAddAutoDeliveryRuleMenu,
) -> None:
    result = await ui_manager.open_menu(
        menu_id=ExtensionMenuIDs.auto_delivery.add_rule_menu,
        context=MenuContext(),
        environment=q,
    )
    await states.AddingAutoDeliveryRule(
        open_session=cbd.session_id,
        delete_message=result.telegram_result.message_id,
    ).set(state)

    with suppress(Exception):
        await q.answer()


@router.callback_query(cbs.AddAutoDeliveryRule.filter())
@router.message(states.AddingAutoDeliveryRule.filter(), lambda m: m.text)
async def add_rule(
    obj: Query | Message,
    state: FSM,
    funpay_props: FunPayProperties,
    ui_manager: UIManager,
    cbd: cbs.AddAutoDeliveryRule | None = None,
) -> None:
    rule = cbd.rule if cbd is not None else obj.text
    if rule in funpay_props.auto_delivery.persistent_subnodes:
        await obj.answer(I18nString('❌ Правило уже существует.'), show_alert=True)

    state_obj = await states.AddingAutoDeliveryRule.clear(state)
    entry = await funpay_props.auto_delivery.add_node(rule)
    await funpay_props.auto_delivery.save()

    session = await ui_manager.session_storage.get(state_obj.open_session)
    await ui_manager.open_menu(
        menu_id=MenuIDs.properties.properties_menu,
        context=NodeMenuContext(node_path=entry.path),
        environment=obj,
        history=session.history + [session.current],
    )


@router.callback_query(cbs.DeleteAutoDeliveryRule.filter())
async def delete_rule(
    q: Query,
    funpay_props: FunPayProperties,
    cbd: cbs.DeleteAutoDeliveryRule,
    ui_manager: UIManager,
) -> None:
    if cbd.rule not in funpay_props.auto_delivery.persistent_subnodes:
        await q.answer(I18nString('❌ Правило не найдено'), show_alert=True)
        return

    await funpay_props.auto_delivery.detach_node_with_hooks(cbd.rule)
    await funpay_props.auto_delivery.save()

    async with ui_manager.edit_session(session_id=cbd.session_id, rerender=True, trigger=q) as s:
        if s.history:
            s.current = s.history.pop()


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
