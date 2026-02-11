from __future__ import annotations


__all__ = [
    'ParameterFlags',
    'PropertiesFlags',
]


from funpayhub.lib.base_app.properties_flags import (
    ParameterFlags as BaseParameterFlags,
    PropertiesFlags as BasePropertiesFlags,
)


class ParameterFlags(BaseParameterFlags): ...


class PropertiesFlags(BasePropertiesFlags): ...
