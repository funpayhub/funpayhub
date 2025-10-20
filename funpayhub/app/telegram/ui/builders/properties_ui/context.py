from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from funpayhub.lib.properties import Properties, MutableParameter
from funpayhub.lib.telegram.ui import MenuContext, ButtonContext


@dataclass(kw_only=True)
class PropertiesMenuContext(MenuContext):
    entry: Properties | MutableParameter[Any]


@dataclass(kw_only=True)
class PropertiesButtonContext(ButtonContext):
    menu_render_context: PropertiesMenuContext
    entry: Properties | MutableParameter[Any]
