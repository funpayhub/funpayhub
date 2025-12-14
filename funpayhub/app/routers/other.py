from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiogram.types import Message

from funpayhub.app.dispatching import Router
from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui.types import MenuContext


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub

router = Router()


sent_event = asyncio.Event()
messages: list[Message] = []


@router.on_telegram_start()
async def send_start_notification(tg_ui: UIRegistry, hub: FunPayHub):
    ctx = MenuContext(
        chat_id=-1,
        menu_id=MenuIds.start_notification,
    )

    menu = await tg_ui.build_menu(ctx)

    async def send_notifications():
        tasks = await hub.telegram.send_notification(
            'system',
            menu.text,
            menu.total_keyboard(True),
        )
        if not tasks:
            sent_event.set()
            return

        done, pending = await asyncio.wait(tasks)
        for task in done:
            if task.exception():
                continue
            result = task.result()
            if isinstance(result, Message):
                messages.append(result)
        sent_event.set()

    asyncio.create_task(send_notifications())


@router.on_funpay_start(as_task=True)
async def edit_start_notifications(tg_ui: UIRegistry, hub: FunPayHub):
    await sent_event.wait()
    for i in messages:
        ctx = MenuContext(menu_id=MenuIds.successful_funpay_start_notification, trigger=i)
        menu = await tg_ui.build_menu(ctx)

        try:
            await i.edit_text(text=menu.text, reply_markup=menu.total_keyboard(True))
        except:
            continue
