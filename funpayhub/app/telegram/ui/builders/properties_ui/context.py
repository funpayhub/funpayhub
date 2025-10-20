from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.telegram.ui import MenuRenderContext, ButtonRenderContext


@dataclass(kw_only=True)
class PropertiesMenuRenderContext(MenuRenderContext):
    entry: Properties | MutableParameter[Any]


@dataclass(kw_only=True)
class PropertiesButtonRenderContext(ButtonRenderContext):
    menu_render_context: PropertiesMenuRenderContext
    entry: Properties | MutableParameter[Any]
