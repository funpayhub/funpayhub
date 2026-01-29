from __future__ import annotations

from dataclasses import dataclass

from funpayhub.lib.telegram.ui import MenuContext, ButtonContext


@dataclass(kw_only=True)
class EntryMenuContext(MenuContext):
    entry_path: list[str]


@dataclass(kw_only=True)
class EntryButtonContext(ButtonContext):
    menu_render_context: EntryMenuContext
    entry_path: list[str]
