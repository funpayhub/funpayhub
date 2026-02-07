from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.app.dispatching import Router


if TYPE_CHECKING:
    from funpayhub.lib.plugins import PluginManager
    from funpayhub.lib.properties import (
        IntParameter,
        ListParameter,
        ChoiceParameter,
        ToggleParameter,
    )
    from funpayhub.lib.translater import Translater

    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram


router = r = Router(name='fph:on_parameter_change_router')


@r.on_parameter_value_changed(
    lambda parameter, properties: parameter is properties.general.language,
    handler_id='fph:change_language',
)
async def change_language(parameter: ChoiceParameter, translater: Translater) -> None:
    translater.current_language = parameter.real_value


@r.on_parameter_value_changed(
    lambda parameter, properties: parameter is properties.toggles.auto_raise,
    handler_id='fph:toggle_auto_raise',
)
async def start_stop_auto_raise(parameter: ToggleParameter, fp: FunPay) -> None:
    if not parameter.value:
        await fp.stop_raising_profile_offers()
    else:
        await fp.start_raising_profile_offers()


@r.on_parameter_value_changed(
    lambda parameter, properties: parameter is properties.telegram.appearance.max_menu_lines,
    handler_id='fph:change_max_menu_lines',
)
async def change_max_menu_lines(parameter: IntParameter, tg: Telegram):
    tg.config.max_menu_lines = parameter.value


@r.on_parameter_value_changed(
    lambda parameter, properties: parameter is properties.plugin_properties.disabled_plugins,
    handler_id='fph:update_disabled_plugins',
)
async def update_disabled_plugins(parameter: ListParameter, plugin_manager: PluginManager):
    plugin_manager._disabled_plugins = set(parameter.value)
