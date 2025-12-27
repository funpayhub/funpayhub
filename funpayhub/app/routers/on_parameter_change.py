from __future__ import annotations

from typing import TYPE_CHECKING

from funpayhub.lib.properties import ChoiceParameter, ToggleParameter
from funpayhub.lib.translater import Translater
from funpayhub.app.dispatching import Router
from funpayhub.app.utils.get_profile_categories import get_profile_raisable_categories


if TYPE_CHECKING:
    from funpayhub.app.funpay.main import FunPay


router = r = Router(name='fph:on_parameter_change_router')


@r.on_parameter_value_changed(
    lambda parameter: parameter.matches_path(['general', 'language']),
    handler_id='fph:change_language',
)
async def change_language(parameter: ChoiceParameter, translater: Translater):
    translater.current_language = parameter.real_value


@r.on_parameter_value_changed(
    lambda parameter: parameter.matches_path(['toggles', 'auto_raise']),
    handler_id='fph:toggle_auto_raise',
)
async def start_stop_auto_raise(parameter: ToggleParameter, fp: FunPay):
    if not parameter.value:
        await fp.offers_raiser.stop_all_raising_loops()
    else:
        categories = await get_profile_raisable_categories(await fp.profile(), fp.bot)
        for category_id in categories:
            await fp.offers_raiser.start_raising_loop(category_id)
