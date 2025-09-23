from dataclasses import dataclass
from io import StringIO


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


class ExecutionResultsRegistry:
    def __init__(self) -> None:
        self.registry: dict[str, ExecutionResult] = {}

    def add_result(
        self,
        id: str,
        code: str,
        error: bool,
        buffer: LockableBuffer
    ) -> ExecutionResult:

        buffer.lock()
        result = ExecutionResult(
            id=id,
            error=error,
            code=code,
            code_len=len(code),
            code_size=len(code.encode('utf-8')),
            buffer_size=len(buffer.getvalue().encode('utf-8')),
            buffer_len=len(buffer.getvalue()),
            buffer=buffer
        )

        self.registry[id] = result
        return result
