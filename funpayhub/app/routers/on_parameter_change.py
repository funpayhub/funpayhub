from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.app.dispatching import Router


if TYPE_CHECKING:
    from funpayhub.lib.plugin import PluginManager
    from pyconfigtree import IntParameter, ListParameter, ChoiceParameter, BoolParameter
    from funpayhub.lib.translater import Translater

    from funpayhub.app.funpay.main import FunPay
    from funpayhub.app.telegram.main import Telegram


router = r = Router(name='fph:on_parameter_change_router')


@r.on_parameter_value_changed(lambda param, props: param is props.general.language)
async def change_language(parameter: ChoiceParameter, translater: Translater) -> None:
    translater.current_language = parameter.value.value


@r.on_parameter_value_changed(lambda param, props: param is props.toggles.auto_raise)
async def start_stop_auto_raise(param: BoolParameter, fp: FunPay) -> None:
    await fp.stop_raising_profile_offers() if param else await fp.start_raising_profile_offers()


@r.on_parameter_value_changed(
    lambda param, props: param is props.telegram.appearance.max_menu_lines,
)
async def change_max_menu_lines(param: IntParameter, tg: Telegram):
    tg.config.max_menu_lines = param.value


@r.on_parameter_value_changed(
    lambda param, props: param is props.plugin_properties.disabled_plugins,
)
async def update_disabled_plugins(param: ListParameter, plugin_manager: PluginManager):
    plugin_manager._disabled_plugins = set(param.value)


@r.on_parameter_value_changed(lambda param, props: param is props.general.runner_request_interval)
async def update_runner_requests_interval(param: IntParameter, fp: FunPay) -> None:
    fp._runner_config.interval = param.value
