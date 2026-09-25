from __future__ import annotations

from aiogram.types import Message
from aiogram.filters import Command
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager, MenuContext
from hubplatform.app.components.telegram.menu_ids import MenuIDs
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext
from hubplatform.app.components.telegram.expressions.builders import ExpressionsListMenuContext


router = Router(name='app:telegram_commands')


@router.message(Command('menu'))
@router.message(Command('start'))
async def send_properties_menu(m: Message, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=MenuIDs.properties.properties_menu,
        context=NodeMenuContext(node_path=[]),
        environment=m,
    )


# todo: remove later
@router.message(Command('sources'))
async def send_sources_menu(m: Message, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=MenuIDs.goods_sources.sources_list_menu,
        context=MenuContext(),
        environment=m,
    )


@router.message(Command('expressions'))
async def send_expressions_list_menu(m: Message, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=MenuIDs.expressions.expressions_list_menu,
        context=ExpressionsListMenuContext(),
        environment=m,
    )
