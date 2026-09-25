from __future__ import annotations

from hubplatform.app import HubPlatformApp
from hubplatform.i18n import global_translator
from hubplatform.goods_source import global_sources_manager
from hubplatform.logging.style import setup_logging
from hubplatform.expressions.registry import global_expressions_registry

from funpayhub.app.properties import FunPayHubProperties
from funpayhub.app.components.funpay import FunPayComponent, FunPayProperties
from funpayhub.app.components.telegram import TelegramComponent, TelegramProperties


setup_logging(global_translator())

_app: HubPlatformApp | None = None


async def main():
    global _app
    props = FunPayHubProperties()
    await props.load()

    telegram_props = TelegramProperties()
    await telegram_props.load()
    telegram_component = TelegramComponent(properties=telegram_props)

    funpay_props = FunPayProperties()
    await funpay_props.load()
    funpay_component = FunPayComponent(properties=funpay_props)

    app = HubPlatformApp(
        version='0.1.0',
        properties=props,
        goods_manager=global_sources_manager(),
        expressions_registry=global_expressions_registry(),
        translator=global_translator(),
        components=[telegram_component, funpay_component],
    )
    _app = app

    await app.setup()
    await app.run()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
