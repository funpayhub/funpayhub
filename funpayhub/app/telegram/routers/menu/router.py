from __future__ import annotations

from aiogram import Router

from .pagination import router as pagination_router


router = Router(name='properties_menu_router')
router.include_router(pagination_router)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from funpayhub.app.telegram.main import Telegram


@router.startup()
async def send_startup_message(tg: Telegram):
    await tg.send_notification('system', 'Бот запущен сучки')