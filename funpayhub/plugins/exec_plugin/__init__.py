from __future__ import annotations

from typing import TYPE_CHECKING

from .types import ExecutionResultsRegistry
from .telegram.menus import (
    exec_code_menu_builder,
    exec_list_menu_builder,
    exec_output_menu_builder,
)
from .telegram.router import r as router


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


class Plugin:
    async def setup(self, hub: FunPayHub) -> None:
        registry = ExecutionResultsRegistry()
        hub.workflow_data['exec_registry'] = registry

        hub.telegram.ui_registry.add_menu('exec_list', exec_list_menu_builder)
        hub.telegram.ui_registry.add_menu('exec_code', exec_code_menu_builder)
        hub.telegram.ui_registry.add_menu('exec_output', exec_output_menu_builder)

        hub.telegram.dispatcher.include_router(router)
