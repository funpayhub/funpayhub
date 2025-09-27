from __future__ import annotations

from enum import Enum, auto


class ParameterFlags(Enum):
    HIDE = auto()
    HIDE_VALUE = auto()
    PROTECT_VALUE = auto()


class PropertiesFlags(Enum):
    HIDE = auto()
    ADDABLE = auto()
