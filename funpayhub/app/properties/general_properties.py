from __future__ import annotations

__all__ = ['GeneralProperties',]


from funpayhub.properties import Properties, ToggleParameter, StringParameter, IntParameter


class GeneralProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name='$props_general:name',
            description='$props_general:description'
        )

        ...
