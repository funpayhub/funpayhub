from aiogram import Router
from funpayhub.app.telegram.middlewares.check_properties_path_exists import CheckPropertiesPathExists, CheckParameterPathExists


router = Router(name='properties_menu_router')

router.callback_query.outer_middleware(CheckPropertiesPathExists())
router.callback_query.outer_middleware(CheckParameterPathExists())
