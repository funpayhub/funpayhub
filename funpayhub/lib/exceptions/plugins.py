from __future__ import annotations


__all__ = [
    'PluginError',
    'PluginInstallationError',
    'PluginInstantiationError',
]

from .base import FunPayHubError


class PluginError(FunPayHubError):
    pass


class PluginInstallationError(PluginError):
    pass


class PluginInstantiationError(PluginError):
    pass
