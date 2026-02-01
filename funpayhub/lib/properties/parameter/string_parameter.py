from __future__ import annotations

from typing import Any
from collections.abc import Callable, Iterable, Awaitable

from funpayhub.lib.properties.parameter.base import MutableParameter
from funpayhub.lib.properties.parameter.converters import string_converter


class StringParameter(MutableParameter[str]):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str,
        default_value: str,
        validator: Callable[[str], Awaitable[None]] | type[Ellipsis] = ...,
        flags: Iterable[Any] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            default_value=default_value,
            validator=validator,
            converter=string_converter,
            flags=flags,
        )
