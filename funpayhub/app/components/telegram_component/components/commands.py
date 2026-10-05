from __future__ import annotations

from aiogram.types import Message
from aiogram.filters import Command
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager, MenuContext
from hubplatform.app.components.telegram.menu_ids import MenuIDs
from hubplatform.app.components.telegram.expressions.builders import ExpressionsListMenuContext

from .notifications_ui.ui import NotificationsMenuContext
from .main_menu_ui.menu_ids import MainMenuUIIds
from .notifications_ui.menu_ids import NotificationsUIMenuIDs


router = Router(name='app:telegram_commands')


@router.message(Command('menu'))
@router.message(Command('start'))
async def send_properties_menu(m: Message, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=MainMenuUIIds.main_menu,
        context=MenuContext(),
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


@router.message(Command('notifications'))
async def send_notifications_menu(m: Message, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=NotificationsUIMenuIDs.current_chat_notifications,
        context=NotificationsMenuContext(category_path=[]),
        environment=m,
    )
