from __future__ import annotations

from dataclasses import dataclass

from funpayhub.lib.telegram.ui import MenuContextModel, ButtonContext


class NodeMenuContext(MenuContextModel):
    entry_path: list[str]


@dataclass(kw_only=True)
class NodeButtonContext(ButtonContext):
    menu_render_context: NodeMenuContext | MenuContextModel
    entry_path: list[str]
