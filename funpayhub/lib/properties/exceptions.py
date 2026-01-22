from __future__ import annotations


__all__ = ['PropertiesError', 'ValidationError', 'ConvertionError']


from funpayhub.lib.core import TranslatableException


class PropertiesError(TranslatableException):
    pass


class ValidationError(PropertiesError):
    pass


class ConvertionError(PropertiesError):
    pass
