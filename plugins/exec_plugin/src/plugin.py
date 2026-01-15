from __future__ import annotations

import os
import json
from pathlib import Path

from funpayhub.lib.plugins import Plugin
from funpayhub.app.telegram.ui.ids import MenuIds

from .types import ExecutionResult, ExecutionResultsRegistry
from .telegram.menus import (
    ExecCodeMenuBuilder,
    ExecListMenuBuilder,
    MainMenuModification,
    ExecOutputMenuBuilder,
)
from .telegram.router import r as router


class ExecPlugin(Plugin):
    async def menus(self):
        return [ExecCodeMenuBuilder, ExecListMenuBuilder, ExecOutputMenuBuilder]

    async def menu_modifications(self):
        return {
            MenuIds.main_menu: MainMenuModification,
        }

    async def telegram_routers(self):
        return router

    async def post_setup(self) -> None:
        registry = ExecutionResultsRegistry()
        self.hub.workflow_data['exec_registry'] = registry
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
