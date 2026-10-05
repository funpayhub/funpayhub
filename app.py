from __future__ import annotations

from typing import Any

from pyconfigtree import BoolParameter, MutableParameter
from hubplatform.app import HubPlatformApp
from hubplatform.i18n import global_translator
from hubplatform.telegram.ui import UIManager
from hubplatform.goods_source import global_sources_manager
from hubplatform.logging.style import setup_logging
from hubplatform.app.dispatching import ParameterValueChangedEvent
from pyconfigtree.parameter.base import ParameterHookTypes
from hubplatform.expressions.registry import global_expressions_registry

from funpayhub.app.properties import FunPayHubProperties
from funpayhub.app.components.funpay_component import FunPayComponent, FunPayProperties
from funpayhub.app.components.telegram_component import TelegramComponent, TelegramProperties


setup_logging(global_translator())

_app: HubPlatformApp | None = None


async def main():
    global _app
    props = FunPayHubProperties()
    await props.load()

    telegram_props = TelegramProperties()
    await telegram_props.load()
    telegram_component = TelegramComponent(properties=telegram_props)
    telegram_component.ui_manager.render_as_inline_keyboard = (
        telegram_props.appearance.render_as_inline_keyboard.value
    )

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
        expressions_registry=global_expressions_registry(),
        translator=global_translator(),
        components=[telegram_component, funpay_component],
    )
    _app = app
    app.properties._hooks[ParameterHookTypes.PARAMETER_VALUE_CHANGED] = tmp

    async def tmp2(telegram_ui_manager: UIManager, parameter: BoolParameter) -> None:
        telegram_ui_manager.render_as_inline_keyboard = parameter.value

    async def tmpfilter(
        parameter: MutableParameter, telegram_properties: TelegramProperties
    ) -> bool:
        return parameter is telegram_properties.appearance.render_as_inline_keyboard

    app.router.on_parameter_value_changed(tmpfilter)(tmp2)

    await app.setup()
    await app.run()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
