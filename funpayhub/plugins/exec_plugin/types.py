from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
import random
import string


class LockableBuffer(StringIO):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._locked = False

    @property
    def locked(self) -> bool:
        return self._locked

    def lock(self) -> None:
        self._locked = True

    def write(self, s, /):
        if self._locked:
            raise RuntimeError('Buffer is locked.')
        super().write(s)

    def writelines(self, lines, /):
        if self._locked:
            raise RuntimeError('Buffer is locked.')
        super().writelines(lines)

    def writable(self) -> bool:
        if self._locked:
            return False
        return super().writable()


@dataclass(frozen=True)
class ExecutionResult:
    id: str
    error: bool
    code: str
    code_len: int
    code_size: int
    buffer_size: int
    buffer_len: int
    buffer: LockableBuffer
    execution_time: float


class ExecutionResultsRegistry:
    def __init__(self) -> None:
        self.registry: dict[str, ExecutionResult] = {}

    def add_result(
        self,
        id: str | None,
        code: str,
        error: bool,
        buffer: LockableBuffer,
        execution_time: float | int,
    ) -> ExecutionResult:
        buffer.lock()
        id = self.make_id(id)

        result = ExecutionResult(
            id=id,
            error=error,
            code=code,
            code_len=len(code),
            code_size=len(code.encode('utf-8')),
            buffer_size=len(buffer.getvalue().encode('utf-8')),
            buffer_len=len(buffer.getvalue()),
            buffer=buffer,
            execution_time=execution_time
        )

        self.registry[id] = result
        return result

    def make_id(self, id: str | None) -> str:
        if not id:
            result = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
            while result in self.registry:
                result = ''.join(
                    random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
            return result

        if id not in self.registry:
            return id

        index = 1
        while id+str(index) in self.registry:
            index += 1
        return id+str(index)
