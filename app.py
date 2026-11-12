from __future__ import annotations

from typing import Any

from pyconfigtree import MutableParameter
from hubplatform.app import HubPlatformApp
from hubplatform.i18n import global_translator
from hubplatform.updates import GitHubVersionsManager
from hubplatform.goods_source import global_sources_manager
from hubplatform.logging.style import setup_logging
from hubplatform.app.dispatching import ParameterValueChangedEvent
from pyconfigtree.parameter.base import ParameterHookTypes

from dothub.app.properties import FunPayHubProperties
from dothub.app.components.funpay_component import FunPayComponent, FunPayProperties
from dothub.app.components.telegram_component import TelegramComponent, TelegramProperties


setup_logging(global_translator())

_app: HubPlatformApp | None = None

REPO_URL = 'https://github.com/funpayhub/funpayhub'


async def main():
    props = FunPayHubProperties()
    await props.load()

    telegram_props = TelegramProperties()
    await telegram_props.load()
    telegram_component = TelegramComponent(properties=telegram_props)

    funpay_props = FunPayProperties()
    await funpay_props.load()
    funpay_component = FunPayComponent(properties=funpay_props)

    async def tmp(param: MutableParameter[Any]):
        event = ParameterValueChangedEvent(parameter=param)
        await app.dispatcher.propagate_event(event=event)

    app = HubPlatformApp(
        version='0.1.0',
        properties=props,
        goods_manager=global_sources_manager(),
        translator=global_translator(),
        components=[telegram_component, funpay_component],
    )

    app.properties._hooks[ParameterHookTypes.PARAMETER_VALUE_CHANGED] = tmp

    async with GitHubVersionsManager(REPO_URL) as versions_manager:
        app.app_context.provide('App', 'versions_manager', versions_manager)
        await app.setup()
        await app.run()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
