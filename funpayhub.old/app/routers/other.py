from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from html import escape

from aiogram.types import Message
from funpaybotengine.types import Category
from eventry.asyncio.filter import all_of

from funpayhub.loggers import main as logger

from funpayhub.lib.translater import en as _en
from funpayhub.lib.telegram.ui.types import MenuContext
from funpayhub.lib.plugin.repository.loaders import URLRepositoryLoader

from funpayhub.app.dispatching import Router
from funpayhub.app.telegram.ui.ids import MenuIds
from funpayhub.app.notification_channels import NotificationChannels
from funpayhub.app.telegram.ui.builders.context import FunPayStartNotificationMenuContext


if TYPE_CHECKING:
    from funpayhub.lib.plugin.repository.manager import RepositoriesManager

    from funpayhub.app.main import FunPayHub
    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram

router = Router()


sent_event = asyncio.Event()
messages: list[Message] = []


@router.on_telegram_start()
async def send_start_notification(hub: FunPayHub) -> None:
    menu = await MenuContext(menu_id=MenuIds.start_notification).build_menu()

    async def send_notifications() -> None:
        tasks = hub.telegram.send_notification(
            NotificationChannels.SYSTEM,
            menu.total_text,
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
async def edit_start_notifications(error: Exception | None) -> None:
    await sent_event.wait()
    for i in messages:
        try:
            await FunPayStartNotificationMenuContext(
                menu_id=MenuIds.funpay_start_notification,
                trigger=i,
                error=error,
            ).apply_to()
        except:
            pass


@router.on_funpay_start(
    all_of(
        lambda error: error is None,
        lambda properties: properties.toggles.auto_raise.value,
    ),
)
async def start_auto_raise(fp: FunPay) -> None:
    logger.info(_en('Starting auto-raising for all profile offers.'))
    await fp.start_raising_profile_offers()


@router.on_offers_raised(lambda properties: properties.telegram.notifications.offers_raised.value)
async def send_offers_raised_notification(category: Category, tg: Telegram) -> None:
    text = f'🔺 Все лоты категории <b>{escape(category.full_name)}</b> успешно подняты.'
    tg.send_notification(NotificationChannels.OFFER_RAISED, text)


@router.on_telegram_start(as_task=True)
async def add_official_plugin_repo(repositories_manager: RepositoriesManager):
    logger.info(_en('Updating official plugins repo.'))
    try:
        repo = await URLRepositoryLoader(
            'https://raw.githubusercontent.com/funpayhub/fph_plugins_repo/refs/heads/master/'
            'com.github.funpayhub.repo.json',
        ).load()
    except:
        logger.error(_en('An error occurred while downloading official repo.'), exc_info=True)
        return

    try:
        repositories_manager.register_repository(repo, overwrite=True, save=True)
    except:
        logger.error(_en('An error occurred while saving official repo.'), exc_info=True)
        return

    logger.info(_en('Successfully updated official plugins repo.'))
