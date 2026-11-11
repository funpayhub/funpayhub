from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import (
    Message,
    CallbackQuery as Query,
)
from aiogram.filters import Command
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager, MenuContext

from dothub.loggers import funpay_component as logger

from . import callbacks as cbs
from ..menu_ids import MenuIDs as ExtensionMenuIDs


if TYPE_CHECKING:
    from dothub.app.components.funpay_component import FunPayComponent


router = Router(name='app:funpay_component:telegram_extension:offers_raiser')


@router.message(Command('auto_raise_ui'))
async def open_offers_raiser_menu(m: Message, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=ExtensionMenuIDs.offers_raiser.main,
        context=MenuContext(),
        environment=m,
    )


@router.callback_query(cbs.UpdateProfile.filter())
async def update_profile(
    q: Query,
    cbd: cbs.UpdateProfile,
    funpay_component: FunPayComponent,
    telegram_ui_manager: UIManager,
) -> None:
    try:
        # Propagates ProfileUpdatedEvent, its handler updates offers raiser.
        await funpay_component.profile(update=True)
    except Exception:
        logger.error('Unable to update FunPay profile.', exc_info=True)
        await q.answer('❌ Не удалось обновить профиль.', show_alert=True)
        return

    await telegram_ui_manager.rerender_session(session_id=cbd.session_id, trigger=q)
    await q.answer('✅ Профиль обновлён.')


@router.callback_query(cbs.RerenderMenu.filter())
async def rerender_menu(q: Query, cbd: cbs.RerenderMenu, telegram_ui_manager: UIManager) -> None:
    await telegram_ui_manager.rerender_session(session_id=cbd.session_id, trigger=q)
    await q.answer()
