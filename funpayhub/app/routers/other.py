from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.lib.translater import Translater
from funpayhub.app.dispatching import Router
from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui.types import MenuContext


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub

router = Router()


@router.on_telegram_start()
async def send_start_notification(translater: Translater, tg_ui: UIRegistry, hub: FunPayHub):
    ctx = MenuContext(
        chat_id=-1,
        menu_id=MenuIds.start_notification,
    )

    menu = await tg_ui.build_menu(ctx)
    await hub.telegram.send_notification('system', menu.text, menu.total_keyboard(True))
