from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from funpayhub.app.telegram import states, callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import UIRegistry, MenuContext
from funpayhub.lib.goods_sources import FileGoodsSource, GoodsSourcesManager
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.callback_data import UnknownCallback, join_callbacks
from funpayhub.app.telegram.ui.builders.properties_ui.context import EntryMenuContext


if TYPE_CHECKING:
    from funpayhub.app.telegram.main import Telegram


r = router = Router(name='fph:auto_delivery')


@router.callback_query(cbs.OpenAddAutoDeliveryRuleMenu.filter())
async def open_add_auto_delivery_rule_menu(
    query: CallbackQuery,
    callback_data: cbs.OpenAddAutoDeliveryRuleMenu,
    tg_ui: UIRegistry,
    state: FSMContext,
):
    """
    Открывает меню добавления правила автовыдачи и активирует состояние `AddingAutoDeliveryRule`.
    """
    msg = await MenuContext(
        trigger=query,
        menu_id=MenuIds.add_auto_delivery_rule,
        callback_override=callback_data.copy_history(
            cbs.OpenMenu(menu_id=MenuIds.add_auto_delivery_rule),
        ),
    ).build_and_apply(tg_ui, query.message)

    state_obj = states.AddingAutoDeliveryRule(message=msg, callback_data=callback_data)
    await state.set_state(state_obj.identifier)
    await state.set_data({'data': state_obj})


@router.callback_query(cbs.AddAutoDeliveryRule.filter())
async def add_auto_delivery_rule(
    query: CallbackQuery,
    translater: Translater,
    properties: FunPayHubProperties,
    callback_data: cbs.AddAutoDeliveryRule,
    tg_ui: UIRegistry,
    state: FSMContext,
):
    """
    Добавляет правило автовыдачи в список параметры.
    Очищает состояние, если оно является `AddingAutoDeliveryRule`.
    Открывает меню настроек правила автовыдачи.
    """
    if callback_data.rule in properties.auto_delivery.entries:
        await query.answer(
            translater.translate('$err_auto_delivery_rule_already_exists'),
            show_alert=True,
        )
        return

    data = await state.get_data()
    if data and isinstance(data.get('data'), states.AddingAutoDeliveryRule):
        await state.clear()

    entry = properties.auto_delivery.add_entry(callback_data.rule)
    await properties.auto_delivery.save()

    await EntryMenuContext(
        trigger=query,
        menu_id=MenuIds.properties_entry,
        entry_path=entry.path,
        callback_override=UnknownCallback.parse(callback_data.pack_history(hash=False)),
    ).build_and_apply(tg_ui, query.message)


@router.message(StateFilter(states.AddingAutoDeliveryRule.identifier))
async def add_auto_delivery_rule_from_message(
    msg: Message,
    state: FSMContext,
    translater: Translater,
    tg_ui: UIRegistry,
    properties: FunPayHubProperties,
):
    """
    Добавляет правило автовыдачи в список параметры.
    Очищает состояние.
    Открывает меню настроек правила автовыдачи.
    """
    if not msg.text:
        return

    if msg.text in properties.auto_delivery.entries:
        await msg.reply(translater.translate('$err_auto_delivery_rule_already_exists'))
        return

    data: states.AddingAutoDeliveryRule = (await state.get_data())['data']
    await state.clear()

    entry = properties.auto_delivery.add_entry(msg.text)
    await properties.auto_delivery.save()

    await EntryMenuContext(
        trigger=msg,
        menu_id=MenuIds.properties_entry,
        entry_path=entry.path,
        callback_override=data.callback_data.copy_history(
            cbs.OpenMenu(
                menu_id=MenuIds.properties_entry,
                context_data={'entry_path': entry.path},
            ),
        ),
    ).build_and_answer(tg_ui, msg)
    await data.message.delete()


@router.callback_query(cbs.DeleteAutoDeliveryRule.filter())
async def delete_auto_delivery_rule(
    query: CallbackQuery,
    properties: FunPayHubProperties,
    callback_data: cbs.DeleteAutoDeliveryRule,
    translater: Translater,
    tg_ui: UIRegistry,
):
    if callback_data.rule not in properties.auto_delivery.entries:
        await query.answer(
            translater.translate('$err_auto_delivery_rule_does_not_exist'),
            show_alert=True,
        )
        return

    properties.auto_delivery.detach_node(callback_data.rule)
    await properties.auto_delivery.save()

    await EntryMenuContext(
        trigger=query,
        menu_id=MenuIds.properties_entry,
        entry_path=properties.auto_delivery.path,
        callback_override=cbs.OpenMenu(
            menu_id=MenuIds.properties_entry,
            context_data={'entry_path': properties.auto_delivery.path},
            #  * > список автовыдачи > меню настроек автовыдачи
            history=callback_data.history[:-2],
        ),
    ).build_and_apply(tg_ui, query.message)


@router.callback_query(cbs.AutoDeliveryOpenGoodsSourcesList.filter())
async def open_bind_goods_menu(
    query: CallbackQuery,
    callback_data: cbs.AutoDeliveryOpenGoodsSourcesList,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
    state: FSMContext,
):
    await EntryMenuContext(
        trigger=query,
        menu_id=MenuIds.autodelivery_goods_sources_list,
        entry_path=properties.auto_delivery.get_properties([callback_data.rule]).path,
    ).build_and_apply(tg_ui, query.message)

    state_obj = states.BindingAutoDeliveryGoodsSource(
        query=query,
        callback_data=callback_data,
        rule=callback_data.rule,
    )
    await state.set_state(state_obj.identifier)
    await state.set_data({'data': state_obj})


@router.callback_query(cbs.BindGoodsSourceToAutoDelivery.filter())
async def bind_goods_source(
    query: CallbackQuery,
    callback_data: cbs.BindGoodsSourceToAutoDelivery,
    properties: FunPayHubProperties,
    state: FSMContext,
    goods_manager: GoodsSourcesManager,
    tg: Telegram,
):
    source = goods_manager.get(callback_data.source_id)
    if source is None:
        await query.answer('$goods_source_does_not_exist', show_alert=True)
        return

    state_str = await state.get_state()
    if state_str == states.BindingAutoDeliveryGoodsSource.identifier:
        await state.clear()

    await (
        properties.auto_delivery.get_properties(
            [callback_data.rule],
        )
        .get_parameter(
            ['goods_source'],
        )
        .set_value(
            callback_data.source_id,
        )
    )

    await tg.execute_previous_callback(
        join_callbacks(*callback_data.history[:-1]),
        query,
    )


INVALID_CHARS = set('<>:"/\\|?*\0')  # todo: code duplicate


@router.message(
    StateFilter(states.BindingAutoDeliveryGoodsSource.identifier),
    lambda msg: msg.text,
)
async def handler(
    message: Message,
    state: FSMContext,
    goods_manager: GoodsSourcesManager,
    translater: Translater,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
):
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
            await message.reply(translater.translate('$err_goods_txt_source_invalid_name'))
            return

        source = await goods_manager.add_source(FileGoodsSource, Path('storage/goods') / filename)

    state_obj: states.BindingAutoDeliveryGoodsSource = (await state.get_data())['data']
    await (
        properties.auto_delivery.get_properties(
            [state_obj.rule],
        )
        .get_parameter(
            ['goods_source'],
        )
        .set_value(source.source_id)
    )

    await state.clear()
    await message.delete()

    await EntryMenuContext(
        trigger=message,
        menu_id=MenuIds.properties_entry,
        entry_path=properties.auto_delivery.get_properties([state_obj.rule]).path,
        callback_override=UnknownCallback.parse(state_obj.callback_data.pack_history(hash=False)),
    ).build_and_answer(tg_ui, message)
    await state_obj.query.message.delete()
