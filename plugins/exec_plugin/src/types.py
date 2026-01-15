from __future__ import annotations

import random
import string
from dataclasses import dataclass


CHARS = string.ascii_letters


@dataclass(frozen=True)
class ExecutionResult:
    id: str
    code: str
    output: str
    error: bool
    execution_time: float

    @property
    def code_len(self) -> int:
        return len(self.code)

    @property
    def code_size(self) -> int:
        return len(self.code.encode('utf-8'))

    @property
    def output_len(self) -> int:
        return len(self.output)

    @property
    def output_size(self) -> int:
        return len(self.output.encode('utf-8'))


class ExecutionResultsRegistry:
    def __init__(self) -> None:
        self.registry: dict[str, ExecutionResult] = {}

    def add_result(
        self,
        id: str | None,
        code: str,
        output: str,
        error: bool,
        execution_time: float | int,
    ) -> ExecutionResult:
        id = self.make_id(id)

        result = ExecutionResult(
            id=id,
            code=code,
            output=output,
            error=error,
            execution_time=execution_time,
        )

        self.registry[id] = result
        return result

    def make_id(self, id: str | None) -> str:
        if not id:
            while True:
                result = ''.join(random.choice(CHARS) for _ in range(10))
                if result not in self.registry:
                    return result

        if id not in self.registry:
            return id

        index = 1
        while id + str(index) in self.registry:
            index += 1
        return id + str(index)
