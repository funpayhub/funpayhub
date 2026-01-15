from __future__ import annotations

import json
import os.path
from typing import TYPE_CHECKING
from pathlib import Path

from .types import ExecutionResult, ExecutionResultsRegistry
from .telegram.menus import (
    ExecCodeMenuBuilder,
    ExecListMenuBuilder,
    ExecOutputMenuBuilder,
    MainMenuModification,
)
from .telegram.router import r as router
from ...app.telegram.ui.ids import MenuIds


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


class Plugin:
    async def setup(self, hub: FunPayHub) -> None:
        registry = ExecutionResultsRegistry()
        folder = Path('.exec')
        if folder.exists() and folder.is_dir():
            for exec_id in os.listdir(folder):
                if not (folder / exec_id).is_dir():
                    continue
                file = folder / exec_id / 'exec.json'
                if not file.exists() or not file.is_file():
                    continue
                try:
                    result = self.load_exec(file)
                    registry.registry[result.id] = result
                except:
                    continue

        hub.workflow_data['exec_registry'] = registry

        hub.telegram.ui_registry.add_menu_builder(ExecListMenuBuilder)
        hub.telegram.ui_registry.add_menu_builder(ExecCodeMenuBuilder)
        hub.telegram.ui_registry.add_menu_builder(ExecOutputMenuBuilder)

        hub.telegram.ui_registry.add_menu_modification(
            MainMenuModification,
            MenuIds.properties_entry,
        )

        hub.telegram.dispatcher.include_router(router)

    def load_exec(self, path: Path) -> ExecutionResult:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        return ExecutionResult(
            id=path.parts[-2],
            code=data['code'],
            output=data['output'],
            error=data['error'],
            execution_time=data['execution_time'],
        )
