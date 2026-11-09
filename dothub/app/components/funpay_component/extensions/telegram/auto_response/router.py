from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager, MenuContext
from hubplatform.app.components.telegram.menu_ids import PropertiesMenuIDs
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext

from .states import AddingAutoResponseRule
from ..menu_ids import MenuIDs as ExtensionMenuIDs
from .callbacks import AddCommand
from ..review_ui.ui import ReviewNotificationContext


if TYPE_CHECKING:
    from dothub.app.components.funpay_component import FunPayProperties


r = router = Router(name='app:funpay_component:auto_response')


@r.callback_query(AddCommand.filter())
async def send_add_auto_response_rule_menu(
    query: CallbackQuery,
    telegram_ui_manager: UIManager,
    state: FSMContext,
    cbd: AddCommand,
) -> None:
    result = await telegram_ui_manager.open_menu(
        menu_id=ExtensionMenuIDs.auto_response.add_rule_menu,
        context=MenuContext(),
        environment=query,
    )

    state_data = AddingAutoResponseRule(
        session_id=result.session.id,
        from_session_id=cbd.session_id,
    )
    await state_data.set(state)
    await query.answer()


@r.message(AddingAutoResponseRule.filter())
async def add_auto_response_rule(
    message: Message,
    telegram_ui_manager: UIManager,
    state: FSMContext,
    funpay_props: FunPayProperties,
) -> None:
    if not message.text:
        return

    if message.text in funpay_props.auto_response.subnodes:
        to_open = funpay_props.auto_response.subnodes[message.text]
    else:
        to_open = await funpay_props.auto_response.add_command_node(message.text)
        await funpay_props.auto_response.save()

    state_data = await AddingAutoResponseRule.clear(state)

    try:
        old_session = await telegram_ui_manager.session_storage.get(state_data.from_session_id)
    except Exception:
        old_session = None

    await telegram_ui_manager.open_menu(
        menu_id=PropertiesMenuIDs.properties_menu,
        context=NodeMenuContext(node_path=to_open.path),
        environment=message,
        history=None if old_session is None else [*old_session.history, old_session.current],
    )
    await telegram_ui_manager.close_session(session_id=state_data.session_id)
