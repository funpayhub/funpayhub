from __future__ import annotations


__all__ = [
    'PropertiesError',
    'ValidationError',
    'ConvertionError',
]

from .base import FunPayHubError


class PropertiesError(FunPayHubError):
    pass


class ValidationError(PropertiesError):
    pass


class ConvertionError(PropertiesError):
    pass
