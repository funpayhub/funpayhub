from __future__ import annotations


__all__ = [
    'ParameterValueChangedEvent',
    'NodeAttachedEvent',
]

from typing import TYPE_CHECKING, Any

from .base import HubEvent


if TYPE_CHECKING:
    from funpayhub.lib.properties import Node, MutableParameter


class ParameterValueChangedEvent(HubEvent, name='fph:parameter_value_changed'):
    def __init__(self, param: MutableParameter[Any]) -> None:
        super().__init__()
        self._parameter = param

    @property
    def event_context_injection(self) -> dict[str, Any]:
        return {
            'parameter': self.parameter,
        }

    @property
    def parameter(self) -> MutableParameter[Any]:
        return self._parameter


class NodeAttachedEvent(HubEvent, name='fph:node_attached'):
    def __init__(self, node: Node) -> None:
        super().__init__()
        self._node = node

    @property
    def event_context_injection(self) -> dict[str, Any]:
        return {
            'node': self.node,
        }

    @property
    def node(self) -> Node:
        return self._node
