from __future__ import annotations


__all__ = [
    'ParameterValueChangedEvent',
    'PropertiesAttachedEvent',
    'ParameterAttachedEvent',
]

from typing import TYPE_CHECKING, Any

from .base import HubEvent


if TYPE_CHECKING:
    from funpayhub.lib.properties import Parameter, Properties, MutableParameter


class ParameterValueChangedEvent(HubEvent):
    def __init__(self, param: MutableParameter):
        super().__init__()
        self.parameter = param

    @property
    def event_context_injection(self) -> dict[str, Any]:
        return {
            'parameter': self.parameter,
        }


class PropertiesAttachedEvent(HubEvent):
    def __init__(self, props: Properties):
        super().__init__()
        self.properties = props

    @property
    def event_context_injection(self) -> dict[str, Any]:
        return {
            'properties': self.properties,
        }


class ParameterAttachedEvent(HubEvent):
    def __init__(self, param: Parameter | MutableParameter):
        super().__init__()
        self.parameter = param

    @property
    def event_context_injection(self) -> dict[str, Any]:
        return {
            'parameter': self.parameter,
        }
