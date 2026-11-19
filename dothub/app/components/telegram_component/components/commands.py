from __future__ import annotations

from aiogram.types import Message
from aiogram.filters import Command
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager, MenuContext

from .main_menu_ui.menu_ids import MainMenuUIIds


router = Router(name='app:telegram_commands')


@router.message(Command('menu'))
@router.message(Command('start'))
async def send_properties_menu(m: Message, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=MainMenuUIIds.main_menu,
        context=MenuContext(),
        environment=m,
    )
