from funpayhub.lib.telegram.ui import MenuRenderContext, ButtonRenderContext
from dataclasses import dataclass
from funpayhub.lib.properties import Properties, MutableParameter
from typing import Any


@dataclass(kw_only=True)
class PropertiesMenuRenderContext(MenuRenderContext):
    entry: Properties | MutableParameter[Any]


@dataclass(kw_only=True)
class PropertiesButtonRenderContext(ButtonRenderContext):
    menu_render_context: PropertiesMenuRenderContext
    entry: Properties | MutableParameter[Any]
