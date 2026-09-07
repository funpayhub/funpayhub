from __future__ import annotations

import os

from hubplatform.app import HubPlatformApp
from hubplatform.i18n import global_translator
from hubplatform.goods_source import global_sources_manager
from hubplatform.logging.style import setup_logging
from hubplatform.expressions.registry import global_expressions_registry
from hubplatform.app.components.telegram.component import TelegramComponent

from funpayhub.app.properties import FunPayHubProperties


setup_logging(global_translator())


# temp --
from hubplatform.telegram import Router
from aiogram.types.message import Message
from aiogram.filters.command import Command
from hubplatform.telegram.ui import UIManager
from hubplatform.app.components.telegram.menu_ids import MenuIDs
from hubplatform.app.components.telegram.properties.builders import NodeMenuContext


r = Router()


@r.message(Command('props'))
async def send_props(m: Message, ui_manager: UIManager) -> None:
    await ui_manager.open_menu(
        menu_id=MenuIDs.properties.properties_menu,
        context=NodeMenuContext(node_path=[]),
        environment=m,
    )


@r.message(Command('stop'))
async def stop(m: Message, app: HubPlatformApp) -> None:
    app.stop()


# -- temp


async def main():
    props = FunPayHubProperties()
    await props.load()

    env_telegram_token = os.environ.get('FUNPAYHUB_TELEGRAM_TOKEN')
    telegram_component = TelegramComponent(
        token=env_telegram_token or props.telegram.bot.token.value,
    )
    telegram_component.dispatcher.include_router(r)

    app = HubPlatformApp(
        version='0.1.0',
        properties=props,
        goods_manager=global_sources_manager(),
        expressions_registry=global_expressions_registry(),
        translator=global_translator(),
        components=[telegram_component],
    )

    await app.setup()
    await app.run()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
