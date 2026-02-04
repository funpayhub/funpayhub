from __future__ import annotations

from dataclasses import dataclass

from funpayhub.lib.telegram.ui import MenuContext, ButtonContext


@dataclass(kw_only=True)
class NodeMenuContext(MenuContext):
    entry_path: list[str]


@dataclass(kw_only=True)
class NodeButtonContext(ButtonContext):
    menu_render_context: NodeMenuContext
    entry_path: list[str]
