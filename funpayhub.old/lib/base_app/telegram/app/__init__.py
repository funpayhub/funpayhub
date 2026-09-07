from __future__ import annotations


__all__ = [
    'ROUTERS',
    'MENUS',
    'BUTTONS',
]

from .ui.router import router as ui_router
from .properties.ui import builders
from .properties.router import router as properties_router


ROUTERS = [ui_router, properties_router]
MENUS = [
    builders.NodeMenuBuilder,
    builders.PropertiesMenuBuilder,
    builders.ChoiceParameterMenuBuilder,
    builders.ListParameterMenuBuilder,
    builders.ParamManualInputMenuBuilder,
    builders.AddListItemMenuBuilder,
]
BUTTONS = [
    builders.NodeButtonBuilder,
    builders.ToggleParamButtonBuilder,
    builders.ChangeParamValueButtonBuilder,
    builders.OpenParamMenuButtonBuilder,
]
