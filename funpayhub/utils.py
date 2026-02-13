from __future__ import annotations

import os
import sys
from typing import Any


IS_WINDOWS = os.name == 'nt'


def exit(code: int) -> None:
    if IS_WINDOWS and sys.stdin.isatty():
        try:
            input('\nPress Enter to exit...')
        except EOFError:
            pass
    sys.exit(code)


def exception_hook(exc_type: type[BaseException], exc: BaseException, tb: Any) -> None:
    sys.__excepthook__(exc_type, exc, tb)
    if IS_WINDOWS:
        try:
            input('\nPress Enter to exit...')
        except EOFError:
            pass


def set_exception_hook() -> None:
    sys.excepthook = exception_hook
