from __future__ import annotations

from typing import Any


__all__ = ['toggle_converter']


def toggle_converter(value: Any) -> bool:
    value = str(value)

    if value.isnumeric():
        return bool(int(value))

    values = {
        'true': True,
        'on': True,
        'off': False,
        'false': False,
        'none': False,
        'null': False,
    }

    if value.lower() in values:
        return values[value.lower()]

    return bool(value)
