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
from funpayhub.lib.properties import Properties
from funpayhub.lib.properties.parameter import StringParameter, ToggleParameter, ListParameter


class ExecPluginProperties(Properties):
    def __init__(self):
        super().__init__(
            id='exec_plugin',
            name='Exec plugin',
            description='Настройки Exec plugin\'а.',
            file='config/exec_plugin.toml'
        )

        self.attach_parameter(
                ToggleParameter(
                    id='test_toggle_parameter',
                    name='Test Toggle Parameter',
                    description='Test Toggle Parameter',
                    default_value=False,
            )
        )

        self.attach_parameter(
            StringParameter(
                id='test_string_parameter',
                name='Test String Parameter',
                description='Test String Parameter',
                default_value='',
            )
        )

        self.attach_parameter(
            ListParameter(
                id='test_list_parameter',
                name='Test List Parameter',
                description='Test List Parameter',
                default_value=[],
            )
        )


class ExecPlugin(Plugin):
    async def properties(self) -> Properties:
        return ExecPluginProperties()

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
