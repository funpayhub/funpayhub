from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


if TYPE_CHECKING:
    pass


class CheckPropertiesPathExists(BaseMiddleware):
    async def __call__(self, handler: Any, event: CallbackQuery, data: dict[str, Any]):
        """
        for i in _PROPS:
            if event.data.startswith(f'{i.__prefix__}{i.__separator__}'):
                break
        else:
            await handler(event, data)
            return

        hub_properties: FunPayHubProperties = data['hub_properties']
        try:
            props = hub_properties.get_properties(i.unpack(event.data).path)
        except LookupError:
            await event.answer('$no_such_props_message')
            return

        data['properties'] = props
        await handler(event, data)
        """
        await handler(event, data)


class CheckParameterPathExists(BaseMiddleware):
    async def __call__(self, handler: Any, event: CallbackQuery, data: dict[str, Any]):
        """
        for i in _PARAMS:
            if event.data.startswith(f'{i.__prefix__}{i.__separator__}'):
                break
        else:
            await handler(event, data)
            return

        hub_properties: FunPayHubProperties = data['hub_properties']
        try:
            props = hub_properties.get_parameter(i.unpack(event.data).path)
        except LookupError:
            await event.answer('$no_such_param_message')
            return

        data['parameter'] = props
        await handler(event, data)
        """

        await handler(event, data)
