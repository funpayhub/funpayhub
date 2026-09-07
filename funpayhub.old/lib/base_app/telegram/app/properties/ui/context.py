from __future__ import annotations

from dataclasses import dataclass

from funpayhub.lib.telegram.ui import MenuContext, ButtonContext


class NodeMenuContext(MenuContext):
    entry_path: list[str]


@dataclass(kw_only=True)
class NodeButtonContext(ButtonContext):
    menu_render_context: NodeMenuContext | MenuContext
    entry_path: list[str]
