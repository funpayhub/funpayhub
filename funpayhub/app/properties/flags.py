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
    def __init__(self, query: str) -> None:
        self._query = query

    @property
    def query(self) -> str:
        return self._query

    def __eq__(self, o: object) -> bool:
        if isinstance(o, type) and issubclass(o, FormattersQueryFlag):
            return True
        if isinstance(o, FormattersQueryFlag):
            return self.query == o.query
        if isinstance(o, str):
            return self.query == o
        return False

    def __hash__(self) -> int:
        return id(self)
