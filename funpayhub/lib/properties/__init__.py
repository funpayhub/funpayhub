"""
Данный модуль содержит классы для создания системы параметров.
"""

from __future__ import annotations


__all__ = [
    'Node',
    'Properties',
    'Parameter',
    'MutableParameter',
    'ToggleParameter',
    'StringParameter',
    'IntParameter',
    'FloatParameter',
    'ListParameter',
    'SetParameter',
    'ChoiceParameter',
]

from .base import Node
from .parameter import *
from .properties import *
