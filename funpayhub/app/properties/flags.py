from __future__ import annotations


__all__ = [
    'ParameterFlags',
    'PropertiesFlags',
    'FormattersQueryFlag',
]


from funpayhub.lib.base_app.properties_flags import (
    ParameterFlags as BaseParameterFlags,
    PropertiesFlags as BasePropertiesFlags,
)


class ParameterFlags(BaseParameterFlags): ...


class PropertiesFlags(BasePropertiesFlags): ...


class FormattersQueryFlag:
    def __init__(self, query: str | None = None) -> None:
        self._query = query

    @property
    def query(self) -> str | None:
        return self._query

    def __hash__(self) -> int:
        return id(self)
