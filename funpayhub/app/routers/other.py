from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from html import escape

from aiogram.types import Message
from funpaybotengine.types import Category

from funpayhub.app.dispatching import Router
from funpayhub.app.telegram.ui.builders.context import FunPayStartNotificationMenuContext
from funpayhub.lib.telegram.ui import UIRegistry
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.lib.telegram.ui.types import MenuContext
from eventry.asyncio.filter import all_of


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram

router = Router()


sent_event = asyncio.Event()
messages: list[Message] = []


@router.on_telegram_start()
async def send_start_notification(tg_ui: UIRegistry, hub: FunPayHub):
    print('ВЫПОЛНЯЮ БЛЯДСКИЙ ХЭНДЛЕР')
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
async def edit_start_notifications(error: Exception | None, tg_ui: UIRegistry, hub: FunPayHub):
    await sent_event.wait()
    for i in messages:
        ctx = FunPayStartNotificationMenuContext(
            menu_id=MenuIds.funpay_start_notification,
            trigger=i,
            error=error
        )
        menu = await tg_ui.build_menu(ctx)

        try:
            await i.edit_text(text=menu.text, reply_markup=menu.total_keyboard(True))
        except:
            continue


@router.on_funpay_start(
    all_of(
        lambda error: error is None,
        lambda properties: properties.toggles.auto_raise.value
    )
)
async def start_auto_raise(fp: FunPay):
    await fp.start_raising_profile_offers()


@router.on_offers_raised(lambda properties: properties.telegram.notifications.offers_raised.value)
async def send_offers_raised_notification(category: Category, tg: Telegram):
    text = f'🔺 Все лоты категории <b>{escape(category.full_name)}</b> успешно подняты.'
    await tg.send_notification('offers_raised', text)
