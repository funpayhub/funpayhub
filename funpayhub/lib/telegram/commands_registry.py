from __future__ import annotations

from dataclasses import dataclass
from collections import ChainMap
from collections.abc import Generator


@dataclass
class Command:
    command: str
    source: str
    setup: bool = False
    description: str | None = None


class CommandsRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, dict[str, Command]] = {}
        self._total_commands: ChainMap[str, Command] = ChainMap()

    def add_command(self, command: Command) -> None:
        if command.command in self._total_commands:
            raise ValueError(f'Command {command.command!r} already exists.')
        if command.source not in self._commands:
            self._commands[command.source] = {}
            self._total_commands = self._total_commands.new_child(self._commands[command.source])
        self._commands[command.source][command.command] = command

    def create_command(
        self,
        command: str,
        source: str,
        setup: bool = False,
        description: str | None = None,
    ) -> Command:
        cmd = Command(command, source, setup, description)
        self.add_command(cmd)
        return cmd

    def commands(self, setup_only: bool = False) -> Generator[Command]:
        for command in self._total_commands.values():
            if not command.setup and setup_only:
                continue
            yield command
