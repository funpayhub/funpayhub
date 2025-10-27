from funpayhub.app.dispatching import Router
from funpayhub.lib.properties import ChoiceParameter
from funpayhub.lib.translater import Translater

router = r = Router()


@r.on_parameter_value_changed(lambda event: event.parameter.matches_path(['general', 'language']))
async def change_language(parameter: ChoiceParameter, translater: Translater):
    translater.current_language = parameter.real_value

