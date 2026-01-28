from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.lib.properties import ChoiceParameter, ToggleParameter
from funpayhub.lib.translater import Translater
from funpayhub.app.dispatching import Router


if TYPE_CHECKING:
    from funpayhub.app.funpay.main import FunPay


router = r = Router(name='fph:on_parameter_change_router')


@r.on_parameter_value_changed(
    lambda parameter: parameter.matches_path(['general', 'language']),
    handler_id='fph:change_language',
)
async def change_language(parameter: ChoiceParameter, translater: Translater) -> None:
    translater.current_language = parameter.real_value


@r.on_parameter_value_changed(
    lambda parameter: parameter.matches_path(['toggles', 'auto_raise']),
    handler_id='fph:toggle_auto_raise',
)
async def start_stop_auto_raise(parameter: ToggleParameter, fp: FunPay) -> None:
    if not parameter.value:
        await fp.stop_raising_profile_offers()
    else:
        await fp.start_raising_profile_offers()
