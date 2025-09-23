from __future__ import annotations

from aiogram import Router

from funpayhub.app.telegram.middlewares.check_properties_path_exists import (
    CheckParameterPathExists,
    CheckPropertiesPathExists,
)


router = Router(name='properties_menu_router')

