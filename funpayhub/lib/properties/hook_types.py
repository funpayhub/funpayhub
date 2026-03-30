from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Any
    from collections.abc import Callable, Awaitable

    from funpayhub.lib.properties import Node, MutableParameter

    type ParameterValueChangedHook = Callable[[MutableParameter], Awaitable[Any]]
    type NodeAttachedHook = Callable[[Node], Awaitable[Any]]
    type NodeDetachedHook = Callable[[Node, Node], Awaitable[Any]]


class HookTypes:
    on_parameter_value_changed = 'on_parameter_value_changed'
    on_node_attached = 'on_node_attached'
    on_node_detached = 'on_node_detached'
